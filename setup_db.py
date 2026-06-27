from app import app
from models import db, User
from werkzeug.security import generate_password_hash

# एपको कन्टेक्स्टभित्र डेटाबेस चलाउने
with app.app_context():
    # १. नयाँ Neon डेटाबेसमा आवश्यक सबै तालिकाहरू (Tables) बनाउने
    db.create_all()
    print("✅ डेटाबेसका सम्पूर्ण तालिकाहरू तयार भए!")

    admin_email = "admin@suryodaya.com"
    new_password = "admin123" 
    
    # २. एड्मिन युजर छ कि छैन चेक गर्ने र बनाउने
    user = User.query.filter_by(email=admin_email).first()
    
    if not user:
        new_admin = User(
            username="Suryodaya_Admin", 
            email=admin_email, 
            password_hash=generate_password_hash(new_password), 
            role="ADMIN"
        )
        db.session.add(new_admin)
        db.session.commit()
        print(f"✅ नयाँ एड्मिन बन्यो! Email: {admin_email}, Password: {new_password}")
    else:
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        print(f"✅ {admin_email} को पासवर्ड '{new_password}' मा रिसेट भयो।")