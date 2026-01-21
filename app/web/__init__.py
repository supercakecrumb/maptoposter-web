"""Web interface blueprint."""

from flask import Blueprint, render_template, session, request
from app.services.theme_service import ThemeService
from app.models import Poster
import uuid

web_bp = Blueprint('web', __name__)


@web_bp.route('/')
def index():
    """Home page with quick create form."""
    theme_service = ThemeService()
    themes = theme_service.get_all_themes()
    return render_template('index.html', themes=themes[:6])  # Show first 6 themes


@web_bp.route('/create')
def create():
    """Full poster creation form."""
    theme_service = ThemeService()
    themes = theme_service.get_all_themes()
    
    # Get optional query parameters for pre-filling
    city = request.args.get('city', '')
    country = request.args.get('country', '')
    distance = request.args.get('distance', type=int)
    theme = request.args.get('theme', '')
    
    return render_template('create.html',
                         themes=themes,
                         prefill_city=city,
                         prefill_country=country,
                         prefill_distance=distance,
                         prefill_theme=theme)


@web_bp.route('/themes')
def themes():
    """Theme gallery page."""
    theme_service = ThemeService()
    all_themes = theme_service.get_all_themes()
    return render_template('themes.html', themes=all_themes)


@web_bp.route('/generate/<job_id>')
def progress(job_id):
    """Job progress tracking page."""
    return render_template('progress.html', job_id=job_id)


@web_bp.route('/batch/<batch_id>')
def batch_progress(batch_id):
    """Batch poster generation progress tracking page."""
    return render_template('batch_progress.html', batch_id=batch_id)


@web_bp.route('/posters/<poster_id>')
def poster_detail(poster_id):
    """Poster detail/result page."""
    poster = Poster.query.get_or_404(poster_id)
    return render_template('result.html', poster=poster)


@web_bp.route('/gallery')
def gallery():
    """User's poster gallery."""
    # Get session ID
    session_id = session.get('session_id')
    
    if not session_id:
        posters = []
    else:
        # Get user's posters
        page = request.args.get('page', 1, type=int)
        pagination = Poster.query.filter_by(session_id=session_id)\
            .order_by(Poster.created_at.desc())\
            .paginate(page=page, per_page=12, error_out=False)
        posters = pagination.items
    
    return render_template('gallery.html', posters=posters if session_id else [])