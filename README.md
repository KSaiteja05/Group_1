Inventory Reservation & Order Locking Service:
A high-performance, secure inventory reservation system built using FastAPI, MongoDB, and async concurrency controls, designed to handle real-world stock reservation, order locking, and expiry scenarios with role-based access control and audit logging.


1. Project Overview
This service enables:

    - Admins to manage products, stock, orders, and system metrics
    - Users to reserve products, commit reservations into orders, or cancel them
    - Automatic expiration of unused reservations
    - Concurrency-safe stock updates
    - JWT-based authentication
    - Complete audit logging for traceability
    - The system is suitable for e-commerce platforms, flash sales, and inventory-critical applications.


2. Key Features
- FastAPI framework for high-performance async API handling
- AsyncIO Locks for concurrency safety
- In-memory reservation store for fast operations
- Persistent MongoDB storage for durability
- Background worker for reservation expiration


3. Technology Stack
    Layer:                Technology:
    Backend               - FastAPI
    Database              - MongoDB
    ODM                   - Motor (Async)
    Authentication        - JWT
    Password Hashing      - PBKDF2
    Async Tasks           - asyncio
    Testing               - pytest, pytest-asyncio
    API Docs              - Swagger (OpenAPI)



4. Authentication & Authorization
Authentication :-
- JWT-based authentication using Bearer tokens
- Tokens include:
   1. user_id
   2. role
   3. expiration timestamp

Authorization :-
    - Role-based access control (admin vs user)
    - Admins have elevated privileges for management endpoints
    - Admins: Product, Stock, Order, and Metrics management
    - Users: Reservation creation, commitment, cancellation and view own data

Dependency enforcement:
    - Depends(require_admin)
    - Depends(require_user)


Product Management (Admin)
Features:-
    - Create products
    - Adjust stock (+ / -)
    - View stock history
    - Public product listing

Stock Safety:-
    - Atomic MongoDB updates
    - Stock history maintained for traceability


Reservation System (User)
Reservation Flow:-

1. User reserves a product
2. Stock is moved:
    - available_stock → reserved_stock

3. Reservation stored in:
    - In-memory store (fast)
    - MongoDB (persistent)


Reservation States:
    - active
    - committed
    - cancelled
    - expired

Concurrency Protection
    - Global asyncio.Lock() ensures race-condition-free reservations


Reservation Expiration Worker
 - A background task runs automatically on startup:
        
        @app.on_event("startup")
        async def startup_event():
            asyncio.create_task(expiration_worker())

- Periodically checks and expires old reservations

What it does?:
    - Runs every 30 seconds
    - Expires stale reservations
    - Restores stock automatically
    - Writes audit logs
    

Order Management
Order Creation:-
    - Orders are created only via committed reservations
    - Ensures:
        - No over-selling
        - Correct pricing
        - Atomic stock reduction

Admin Controls:
    - Update order status
    - View all orders

User Controls
    - View only their own orders

5. Dependencies
    - Install all required dependencies using:

    ```bash
        pip install -r requirements.txt
    ```

6. How to Run the Application
    - Clone the Repository
        git clone https://github.com/<your-username>/<repository-name>.git
        cd <repository-name>

    - Create and Activate Virtual Environment
    ```bash
        python -m venv venv
        venv\Scripts\activate ( Windows )
        source venv/bin/activate ( macOS/Linux )
    ```

    - Configure Environment Variables
        Create a .env file in the project root:
        ```
            DATABASE_URL=sqlite:///./app.db
            SECRET_KEY=your_secret_key
            ALGORITHM=HS256
            ACCESS_TOKEN_EXPIRE_MINUTES=60
        ```

    - Start MongoDB
            mongod

    - Start the Server
        ```
            uvicorn app.main:app --reload
        ```


7. API Documentation
    Once running, access:

    Swagger UI:
       http://127.0.0.1:8000/docs

    ReDoc:
       http://127.0.0.1:8000/redoc


8. API Overview
    Public APIs
    - List products
    - View product details
    - Health check

    User APIs
    - Create reservation
    - View reservations
    - Commit / cancel reservation
    - View own orders

    Admin APIs
    - Create products
    - Adjust stock
    - View stock history
    - View all orders
    - Update order status
    - Metrics & audit logs

9. Testing Strategy & Coverage
    Tools Used
    - pytest
    - pytest-asyncio

    Tests Include
    - Auth validation
    - Stock updates
    - Reservation creation
    - Concurrent reservation attempts
    - Expiry handling
    - Order commit flow

    Running Tests
        ```bash
            pytest -v
        ```
10. Audit Logging System
    Why Audit Logs Matter
    - Debugging
    - Compliance
    - Traceability
    - Admin accountability

    Logged Events Include
    - Product creation
    - Stock updates
    - Reservation creation
    - Expiration
    - Cancellation
    - Order commits
    - Order status changes

    Each audit log contains:
    - Event type
    - Entity info
    - User
    - Timestamp
    - Change details

11. Concurrency & Data Integrity
    Key Techniques Used
    - asyncio.Lock() for reservation operations
    - MongoDB atomic updates
    - Status validation before every action

    Why This Is Safe
    - Prevents double-reservation
    - Prevents overselling
    - Prevents stale writes
    - Ensures accurate stock levels


12. Performance & Scalability Notes
    - Async non-blocking IO
    - MongoDB handles high read/write throughput
    - In-memory reservations reduce DB load
    - Suitable for moderate-to-high traffic systems


13. Limitations & Assumptions
    - In-memory store is process-local
    - Single instance recommended (or use Redis for scale)
    - Payment is simulated (not integrated)
