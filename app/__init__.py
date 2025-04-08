from .database import MongoDB

# Initialize MongoDB connection when the app starts
def startup_event():
    print("Initializing MongoDB connection pool...")
    # Connection will be established on first request

def shutdown_event():
    print("Closing MongoDB connections...")
    MongoDB.close()

# Corrected: Double underscores for __all__
__all__ = ["MongoDB"]  # Explicit exports