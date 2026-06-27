from app import app
from models import db, User
from werkzeug.security import generate_password_hash

# एपको कन्टेक्स्टभित्र डेटाबेस चलाउने
with app.app_context():
    admin_email = "admin@suryodaya.com"
    new_password = "admin123" # तपाईंलाई याद हुने नयाँ पासवर्ड राख्नुहोस्
    
    # डेटाबेसमा यो इमेल भएको युजर खोज्ने
    user = User.query.filter_by(email=admin_email).first()
    
    if user:
        # युजर भेटिएमा पासवर्ड परिवर्तन गर्ने
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        print(f"सफल भयो! {admin_email} को पासवर्ड '{new_password}' मा रिसेट भयो।")
    else:
        # युजर नभेटिएमा नयाँ एड्मिन बनाउने
        new_admin = User(
            username="Suryodaya_Admin", 
            email=admin_email, 
            password_hash=generate_password_hash(new_password), 
            role="ADMIN"
        )
        db.session.add(new_admin)
        db.session.commit()
        print(f"नयाँ एड्मिन बन्यो! Email: {admin_email}, Password: {new_password}")