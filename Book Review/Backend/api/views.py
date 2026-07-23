import json
from datetime import datetime, time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Count, Q
from django.utils import timezone
from api.models import User, Book, Review
from api.helpers import generate_token

# Helper to check auth status
def get_auth_user(request):
    if request.user.is_authenticated:
        return request.user
    return None

def require_admin(request):
    user = get_auth_user(request)
    return user and user.role == 'admin'

# --- Auth Views ---
@csrf_exempt
def register_view(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only POST method allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not email or not password:
            return JsonResponse({'success': False, 'message': 'Missing required fields'}, status=400)
        
        if User.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': 'Email already exists'}, status=400)
            
        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'message': 'Username already exists'}, status=400)
            
        user = User.objects.create_user(email=email, username=username, password=password)
        return JsonResponse({'success': True, 'message': 'Registration successful'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
def login_view(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only POST method allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return JsonResponse({'success': False, 'message': 'Email and password required'}, status=400)
            
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid credentials!'}, status=401)
            
        if not user.check_password(password):
            return JsonResponse({'success': False, 'message': 'Invalid credentials!'}, status=401)
            
        if user.status == 'suspended':
            return JsonResponse({'success': False, 'message': 'Your account has been suspended!'}, status=403)
            
        # Update last login
        user.last_login = timezone.now()
        user.save()
        
        token = generate_token(user)
        return JsonResponse({
            'success': True,
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
def profile_view(request):
    user = get_auth_user(request)
    if not user:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=401)
        
    if request.method == 'GET':
        user_reviews = Review.objects.filter(user=user)
        total_reviews = user_reviews.count()
        books_read = user_reviews.values('book').distinct().count()
        avg_rating = user_reviews.aggregate(Avg('rating'))['rating__avg'] or 0.0
        helpful_votes = total_reviews * 3  # Mock value
        
        recent_reviews = []
        for review in user_reviews.order_by('-created_at')[:5]:
            recent_reviews.append({
                'id': review.id,
                'bookId': review.book.id,
                'bookTitle': review.book.title,
                'rating': review.rating,
                'comment': review.comment,
                'date': review.created_at.strftime('%Y-%m-%d')
            })
            
        return JsonResponse({
            'success': True,
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'joinDate': user.join_date.strftime('%Y-%m-%d') if user.join_date else 'Recently',
            'stats': {
                'totalReviews': total_reviews,
                'booksRead': books_read,
                'avgRating': float(round(avg_rating, 1)),
                'helpfulVotes': helpful_votes
            },
            'reviews': recent_reviews
        })
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

# --- Books Views ---
@csrf_exempt
def books_list_create_view(request):
    if request.method == 'GET':
        query = Book.objects.annotate(
            avg_rating=Avg('reviews__rating'),
            total_reviews=Count('reviews')
        )
        
        # Search & Filter
        title_q = request.GET.get('title')
        author_q = request.GET.get('author')
        genre_q = request.GET.get('genre')
        search_q = request.GET.get('search')  # general search
        
        if title_q:
            query = query.filter(title__icontains=title_q)
        if author_q:
            query = query.filter(author__icontains=author_q)
        if genre_q:
            query = query.filter(genre__iexact=genre_q)
        if search_q:
            query = query.filter(
                Q(title__icontains=search_q) |
                Q(author__icontains=search_q) |
                Q(genre__icontains=search_q)
            )
            
        books_data = []
        for book in query.order_by('id'):
            books_data.append({
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'genre': book.genre,
                'published_date': book.published_date.strftime('%Y-%m-%d') if book.published_date else None,
                'cover_url': book.cover_url,
                'description': book.description,
                'avg_rating': float(round(book.avg_rating, 1)) if book.avg_rating else 0.0,
                'total_reviews': book.total_reviews
            })
        return JsonResponse({'books': books_data})
        
    elif request.method == 'POST':
        if not require_admin(request):
            return JsonResponse({'success': False, 'message': 'Admin privilege required'}, status=403)
            
        try:
            if request.content_type.startswith('multipart/form-data'):
                title = request.POST.get('title')
                author = request.POST.get('author')
                genre = request.POST.get('genre')
                published_date_str = request.POST.get('published_date')
                description = request.POST.get('description')
                
                cover_image = request.FILES.get('cover_image')
                cover_url = ''
                if cover_image:
                    from django.core.files.storage import default_storage
                    from django.core.files.base import ContentFile
                    from django.conf import settings
                    file_name = default_storage.save(f'book_covers/{cover_image.name}', ContentFile(cover_image.read()))
                    cover_url = request.build_absolute_uri(settings.MEDIA_URL + file_name)
            else:
                data = json.loads(request.body)
                title = data.get('title')
                author = data.get('author')
                genre = data.get('genre')
                published_date_str = data.get('published_date')
                cover_url = data.get('cover_url')
                description = data.get('description')
            
            if not title or not author or not genre:
                return JsonResponse({'success': False, 'message': 'Title, Author, and Genre are required'}, status=400)
                
            published_date = None
            if published_date_str:
                try:
                    published_date = datetime.strptime(published_date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
                    
            book = Book.objects.create(
                title=title,
                author=author,
                genre=genre,
                published_date=published_date,
                cover_url=cover_url,
                description=description
            )
            
            return JsonResponse({
                'success': True,
                'book': {
                    'id': book.id,
                    'title': book.title,
                    'author': book.author,
                    'genre': book.genre,
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
            
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def book_detail_view(request, book_id):
    try:
        book = Book.objects.annotate(
            avg_rating=Avg('reviews__rating'),
            total_reviews=Count('reviews')
        ).get(id=book_id)
    except Book.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Book not found'}, status=404)
        
    if request.method == 'GET':
        return JsonResponse({
            'success': True,
            'book': {
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'genre': book.genre,
                'published_date': book.published_date.strftime('%Y-%m-%d') if book.published_date else None,
                'cover_url': book.cover_url,
                'description': book.description,
                'avg_rating': float(round(book.avg_rating, 1)) if book.avg_rating else 0.0,
                'total_reviews': book.total_reviews
            }
        })
        
    elif request.method in ['PUT', 'POST']:
        if not require_admin(request):
            return JsonResponse({'success': False, 'message': 'Admin privilege required'}, status=403)
            
        try:
            if request.content_type.startswith('multipart/form-data'):
                title = request.POST.get('title', book.title)
                author = request.POST.get('author', book.author)
                genre = request.POST.get('genre', book.genre)
                published_date_str = request.POST.get('published_date')
                description = request.POST.get('description', book.description)
                
                cover_image = request.FILES.get('cover_image')
                if cover_image:
                    from django.core.files.storage import default_storage
                    from django.core.files.base import ContentFile
                    from django.conf import settings
                    file_name = default_storage.save(f'book_covers/{cover_image.name}', ContentFile(cover_image.read()))
                    book.cover_url = request.build_absolute_uri(settings.MEDIA_URL + file_name)
            else:
                data = json.loads(request.body)
                title = data.get('title', book.title)
                author = data.get('author', book.author)
                genre = data.get('genre', book.genre)
                published_date_str = data.get('published_date')
                book.cover_url = data.get('cover_url', book.cover_url)
                description = data.get('description', book.description)
                
            book.title = title
            book.author = author
            book.genre = genre
            book.description = description
            
            if request.content_type.startswith('multipart/form-data'):
                if 'published_date' in request.POST:
                    pub_str = request.POST.get('published_date')
                    if pub_str:
                        try:
                            book.published_date = datetime.strptime(pub_str, '%Y-%m-%d').date()
                        except ValueError:
                            pass
                    else:
                        book.published_date = None
            else:
                if 'published_date' in data:
                    pub_str = data.get('published_date')
                    if pub_str:
                        try:
                            book.published_date = datetime.strptime(pub_str, '%Y-%m-%d').date()
                        except ValueError:
                            pass
                    else:
                        book.published_date = None
                        
            book.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
            
    elif request.method == 'DELETE':
        if not require_admin(request):
            return JsonResponse({'success': False, 'message': 'Admin privilege required'}, status=403)
        book.delete()
        return JsonResponse({'success': True})
        
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

# --- Reviews Views ---
@csrf_exempt
def book_reviews_view(request, book_id):
    try:
        book = Book.objects.get(id=book_id)
    except Book.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Book not found'}, status=404)
        
    if request.method == 'GET':
        reviews = Review.objects.filter(book=book).order_by('-created_at')
        reviews_data = []
        for review in reviews:
            reviews_data.append({
                'id': review.id,
                'username': review.user.username,
                'user_id': review.user.id,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at.strftime('%Y-%m-%d')
            })
        return JsonResponse({'reviews': reviews_data})
        
    elif request.method == 'POST':
        user = get_auth_user(request)
        if not user:
            return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=401)
            
        try:
            data = json.loads(request.body)
            rating = data.get('rating')
            comment = data.get('comment')
            
            if rating is None or not comment:
                return JsonResponse({'success': False, 'message': 'Rating and comment are required'}, status=400)
                
            review = Review.objects.create(
                book=book,
                user=user,
                rating=int(rating),
                comment=comment
            )
            return JsonResponse({
                'success': True,
                'review': {
                    'id': review.id,
                    'rating': review.rating,
                    'comment': review.comment,
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
            
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def review_detail_view(request, review_id):
    try:
        review = Review.objects.get(id=review_id)
    except Review.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Review not found'}, status=404)
        
    user = get_auth_user(request)
    if not user:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=401)
        
    if request.method == 'PUT':
        # Only the review author can edit
        if review.user.id != user.id:
            return JsonResponse({'success': False, 'message': 'Forbidden'}, status=403)
            
        try:
            data = json.loads(request.body)
            comment = data.get('comment')
            if not comment:
                return JsonResponse({'success': False, 'message': 'Comment is required'}, status=400)
            review.comment = comment
            review.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
            
    elif request.method == 'DELETE':
        # Author or admin can delete
        if review.user.id != user.id and user.role != 'admin':
            return JsonResponse({'success': False, 'message': 'Forbidden'}, status=403)
            
        review.delete()
        return JsonResponse({'success': True})
        
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def all_reviews_list_view(request):
    # Public endpoint to fetch all reviews with filters
    if request.method == 'GET':
        reviews = Review.objects.select_related('book', 'user').order_by('-created_at')
        
        book_title_filter = request.GET.get('book_title')
        rating_filter = request.GET.get('rating')
        
        if book_title_filter and book_title_filter != 'all':
            reviews = reviews.filter(book__title=book_title_filter)
        if rating_filter and rating_filter != 'all':
            reviews = reviews.filter(rating=int(rating_filter))
            
        reviews_data = []
        for r in reviews:
            reviews_data.append({
                'id': r.id,
                'bookId': r.book.id,
                'bookTitle': r.book.title,
                'username': r.user.username,
                'userId': r.user.id,
                'rating': r.rating,
                'comment': r.comment,
                'date': r.created_at.strftime('%Y-%m-%d')
            })
        return JsonResponse({'reviews': reviews_data})
        
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

# --- Admin Views ---
@csrf_exempt
def admin_dashboard_view(request):
    if not require_admin(request):
        return JsonResponse({'success': False, 'message': 'Admin privilege required'}, status=403)
        
    if request.method == 'GET':
        total_books = Book.objects.count()
        total_users = User.objects.count()
        total_reviews = Review.objects.count()
        
        today_start = timezone.make_aware(datetime.combine(timezone.now().date(), time.min))
        reviews_today = Review.objects.filter(created_at__gte=today_start).count()
        
        # Build activities dynamically
        recent_activity = []
        
        # Latest reviews
        latest_reviews = Review.objects.select_related('book', 'user').order_by('-created_at')[:4]
        for review in latest_reviews:
            delta = timezone.now() - review.created_at
            time_str = "just now"
            if delta.days > 0:
                time_str = f"{delta.days} days ago"
            elif delta.seconds >= 3600:
                time_str = f"{delta.seconds // 3600} hours ago"
            elif delta.seconds >= 60:
                time_str = f"{delta.seconds // 60} minutes ago"
                
            recent_activity.append({
                'time': time_str,
                'text': f"New review added for \"{review.book.title}\" by {review.user.username}",
                'timestamp': review.created_at
            })
            
        # Latest registrations
        latest_users = User.objects.order_by('-join_date')[:4]
        for user in latest_users:
            delta = timezone.now() - user.join_date
            time_str = "just now"
            if delta.days > 0:
                time_str = f"{delta.days} days ago"
            elif delta.seconds >= 3600:
                time_str = f"{delta.seconds // 3600} hours ago"
            elif delta.seconds >= 60:
                time_str = f"{delta.seconds // 60} minutes ago"
                
            recent_activity.append({
                'time': time_str,
                'text': f"New user registered: {user.email}",
                'timestamp': user.join_date
            })
            
        # Sort activities by timestamp
        recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
        # Format list to remove timestamp objects
        formatted_activity = [{ 'time': a['time'], 'text': a['text'] } for a in recent_activity[:10]]
        
        return JsonResponse({
            'success': True,
            'stats': {
                'total_books': total_books,
                'total_users': total_users,
                'total_reviews': total_reviews,
                'reviews_today': reviews_today
            },
            'recent_activity': formatted_activity
        })
        
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def admin_reviews_list_view(request):
    if not require_admin(request):
        return JsonResponse({'success': False, 'message': 'Admin privilege required'}, status=403)
        
    if request.method == 'GET':
        reviews = Review.objects.select_related('book', 'user').order_by('-created_at')
        reviews_data = []
        for r in reviews:
            reviews_data.append({
                'id': r.id,
                'username': r.user.username,
                'book_title': r.book.title,
                'rating': r.rating,
                'comment': r.comment,
                'created_at': r.created_at.strftime('%Y-%m-%d')
            })
        return JsonResponse({'reviews': reviews_data})
        
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def admin_review_detail_view(request, review_id):
    if not require_admin(request):
        return JsonResponse({'success': False, 'message': 'Admin privilege required'}, status=403)
        
    try:
        review = Review.objects.get(id=review_id)
    except Review.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Review not found'}, status=404)
        
    if request.method == 'DELETE':
        review.delete()
        return JsonResponse({'success': True})
        
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def admin_users_list_view(request):
    if not require_admin(request):
        return JsonResponse({'success': False, 'message': 'Admin privilege required'}, status=403)
        
    if request.method == 'GET':
        users = User.objects.annotate(reviews_count=Count('reviews')).order_by('id')
        users_data = []
        for u in users:
            users_data.append({
                'id': u.id,
                'username': u.username,
                'email': u.email,
                'role': u.role,
                'status': u.status,
                'join_date': u.join_date.strftime('%Y-%m-%d') if u.join_date else 'N/A',
                'reviews_count': u.reviews_count
            })
        return JsonResponse({'users': users_data})
        
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def admin_user_toggle_status_view(request, user_id):
    if not require_admin(request):
        return JsonResponse({'success': False, 'message': 'Admin privilege required'}, status=403)
        
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found'}, status=404)
        
    if request.method == 'POST':
        # Don't allow suspending oneself
        if user.id == request.user.id:
            return JsonResponse({'success': False, 'message': 'Cannot modify your own status'}, status=400)
            
        user.status = 'suspended' if user.status == 'active' else 'active'
        user.save()
        return JsonResponse({'success': True, 'status': user.status})
        
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def admin_user_delete_view(request, user_id):
    if not require_admin(request):
        return JsonResponse({'success': False, 'message': 'Admin privilege required'}, status=403)
        
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found'}, status=404)
        
    if request.method == 'DELETE':
        if user.id == request.user.id:
            return JsonResponse({'success': False, 'message': 'Cannot delete your own admin account'}, status=400)
        user.delete()
        return JsonResponse({'success': True})
        
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def admin_make_user_admin_view(request, user_id):
    if not require_admin(request):
        return JsonResponse({'success': False, 'message': 'Admin privilege required'}, status=403)
        
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found'}, status=404)
        
    if request.method == 'POST':
        if user.role == 'admin':
            return JsonResponse({'success': False, 'message': 'User is already an Admin.'}, status=400)
            
        user.role = 'admin'
        user.save()
        return JsonResponse({'success': True, 'message': f'User {user.username} has been promoted to Admin successfully.'})
        
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def admin_demote_user_view(request, user_id):
    if not require_admin(request):
        return JsonResponse({'success': False, 'message': 'Admin privilege required'}, status=403)
        
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found'}, status=404)
        
    if request.method == 'POST':
        if user.role == 'user':
            return JsonResponse({'success': False, 'message': 'User is already a normal user.'}, status=400)
            
        user.role = 'user'
        user.save()
        return JsonResponse({'success': True, 'message': f'User {user.username} has been demoted to normal user successfully.'})
        
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

