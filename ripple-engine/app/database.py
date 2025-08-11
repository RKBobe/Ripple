from sqlmodel import create_engine

# Define the database file name
SQLITE_FILE_NAME = "database.db"
# Define the connection URL
sqlite_url = f"sqlite:///{SQLITE_FILE_NAME}"

# Create the database engine
# The 'connect_args' is needed specifically for SQLite to allow it to be
# accessed by multiple threads, which is how FastAPI runs.
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})