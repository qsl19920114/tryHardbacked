#!/usr/bin/env python3
"""
Script to update existing script records to use the new auto-generated cover path format.
This script will update all existing scripts to have cover paths in the format /static/images/{id}.jpg
"""

from app.database import SessionLocal
from app.models.database_models import Script

def update_cover_paths():
    """Update all existing script records to use the new cover path format"""
    db = SessionLocal()
    
    try:
        # Get all scripts from the database
        scripts = db.query(Script).all()
        
        print(f"Found {len(scripts)} scripts to update...")
        
        updated_count = 0
        for script in scripts:
            old_cover = script.cover
            new_cover = f"/static/images/{script.id}.jpg"
            
            if old_cover != new_cover:
                script.cover = new_cover
                updated_count += 1
                print(f"Updated script {script.id} ({script.title}): {old_cover} -> {new_cover}")
        
        # Commit all changes
        db.commit()
        print(f"\nSuccessfully updated {updated_count} script cover paths.")
        
        # Verify the changes
        print("\nVerifying updates...")
        scripts = db.query(Script).all()
        for script in scripts:
            print(f"Script {script.id}: {script.cover}")
            
    except Exception as e:
        print(f"Error updating cover paths: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Updating script cover paths to new format...")
    update_cover_paths()
    print("Update complete!")
