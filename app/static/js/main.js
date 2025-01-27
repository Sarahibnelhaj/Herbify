// Function to check if the user is authenticated
function checkAuth() {
    const token = localStorage.getItem('access_token');
    const userRole = localStorage.getItem('user_role');

    if (!token) {
        window.location.href = '/login';
    }
    return { token, userRole };
}

// Function to handle user login
async function loginUser(event) {
    event.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    const response = await fetch('/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
    });
    const data = await response.json();

    if (response.ok) {
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('user_role', data.role);
        alert('Logged in successfully');
        window.location.href = '/dashboard'; // Redirect to dashboard
    } else {
        alert('Login failed: ' + data.error);
    }
}

// Function to handle user registration
async function registerUser(event) {
    event.preventDefault();
    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const role = document.getElementById('role').value;

    const response = await fetch('/auth/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, email, password, role }),
    });
    const data = await response.json();

    if (response.ok) {
        alert('Registration successful! Please login.');
        window.location.href = '/login';
    } else {
        alert('Registration failed: ' + data.error);
    }
}

// Function to handle user logout
function logoutUser() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_role');
    alert('Logged out successfully');
    window.location.href = '/';
}

// Function to fetch and display research history
async function fetchResearchHistory() {
    const { token } = checkAuth();
    const response = await fetch('/auth/research/history', {
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });
    const data = await response.json();

    if (response.ok) {
        const researchHistoryContainer = document.getElementById('research-history');
        if (data.research_history.length > 0) {
            researchHistoryContainer.innerHTML = data.research_history.map(herb => `
                <div class="card mb-3">
                    <div class="card-body">
                        <h5 class="card-title">${herb.common_name}</h5>
                        <p class="card-text"><strong>Scientific Name:</strong> ${herb.scientific_name}</p>
                        <p class="card-text"><strong>Part Used:</strong> ${herb.part_used}</p>
                        <p class="card-text"><strong>Toxicity:</strong> ${herb.toxicity}</p>
                    </div>
                </div>
            `).join('');
        } else {
            researchHistoryContainer.innerHTML = `<p>No research history found.</p>`;
        }
    } else {
        alert('Failed to fetch research history: ' + data.error);
    }
}

// Function to identify a plant
async function identifyPlant(event) {
    event.preventDefault();
    const { token } = checkAuth();
    const imageUrl = document.getElementById('image_url').value;

    const response = await fetch('/auth/research/identify-plant', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ image_url: imageUrl }),
    });
    const data = await response.json();

    if (response.ok) {
        document.getElementById('identified-plant').innerHTML = `
            <div class="alert alert-success">
                <strong>Identified Plant:</strong> ${data.herb.common_name} (${data.herb.scientific_name})
            </div>
        `;
        fetchResearchHistory(); // Refresh the research history
    } else {
        alert('Failed to identify plant: ' + data.error);
    }
}

// Function to fetch and display marketplace products
async function fetchMarketplace() {
    const { token } = checkAuth();
    const response = await fetch('/auth/marketplace', {
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });
    const data = await response.json();

    if (response.ok) {
        const productsContainer = document.getElementById('products-container');
        productsContainer.innerHTML = data.products.map(product => `
            <div class="col-md-4 mb-4">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">${product.name}</h5>
                        <p class="card-text"><strong>Price:</strong> $${product.price}</p>
                        <p class="card-text"><strong>Description:</strong> ${product.description}</p>
                    </div>
                </div>
            </div>
        `).join('');
    } else {
        alert('Failed to fetch marketplace: ' + data.error);
    }
}

// Function to add a product (for sellers)
async function addProduct(event) {
    event.preventDefault();
    const { token, userRole } = checkAuth();

    if (userRole !== 'seller') {
        alert('You do not have permission to add products.');
        return;
    }

    const productData = {
        name: document.getElementById('name').value,
        description: document.getElementById('description').value,
        price: parseFloat(document.getElementById('price').value),
        stock: parseInt(document.getElementById('stock').value),
    };

    const response = await fetch('/auth/products', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(productData),
    });
    const data = await response.json();

    if (response.ok) {
        alert('Product added successfully');
        fetchMarketplace(); // Refresh the product list
    } else {
        alert('Failed to add product: ' + data.error);
    }
}

// Function to fetch and display all users (for admins)
async function fetchAllUsers() {
    const { token } = checkAuth();
    const response = await fetch('/admin/users', {
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });
    const data = await response.json();

    if (response.ok) {
        const usersContainer = document.getElementById('all-users');
        usersContainer.innerHTML = data.users.map(user => `
            <p>${user.username} (${user.role})</p>
        `).join('');
    } else {
        alert('Failed to fetch users: ' + data.error);
    }
}


// Fetch all herbs (for herbs.html)
async function fetchAllHerbs() {
    const { token } = checkAuth();
    const response = await fetch('/api/herbs', {
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });
    const data = await response.json();

    if (response.ok) {
        const herbsContainer = document.getElementById('herbs-container');
        herbsContainer.innerHTML = data.herbs.map(herb => `
            <div class="col-md-4 mb-4">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">${herb.common_name}</h5>
                        <p class="card-text"><strong>Scientific Name:</strong> ${herb.scientific_name}</p>
                        <p class="card-text"><strong>Part Used:</strong> ${herb.part_used}</p>
                        <p class="card-text"><strong>Toxicity:</strong> ${herb.toxicity}</p>
                    </div>
                </div>
            </div>
        `).join('');
    } else {
        alert('Failed to fetch herbs: ' + data.error);
    }
}

// Fetch all products (for products.html)
async function fetchMarketplace() {
    const { token } = checkAuth();
    const response = await fetch('/api/products', {
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });
    const data = await response.json();

    if (response.ok) {
        const productsContainer = document.getElementById('products-container');
        productsContainer.innerHTML = data.products.map(product => `
            <div class="col-md-4 mb-4">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">${product.name}</h5>
                        <p class="card-text"><strong>Price:</strong> $${product.price}</p>
                        <p class="card-text"><strong>Description:</strong> ${product.description}</p>
                    </div>
                </div>
            </div>
        `).join('');
    } else {
        alert('Failed to fetch products: ' + data.error);
    }
}

// Fetch user's herbs (for researchers)
async function fetchUserHerbs() {
    const { token } = checkAuth();
    const response = await fetch('/api/user/herbs', {
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });
    const data = await response.json();

    if (response.ok) {
        const userHerbsContainer = document.getElementById('user-herbs');
        userHerbsContainer.innerHTML = data.herbs.map(herb => `
            <div class="mb-3">
                <h5>${herb.common_name}</h5>
                <p><strong>Scientific Name:</strong> ${herb.scientific_name}</p>
                <p><strong>Part Used:</strong> ${herb.part_used}</p>
            </div>
        `).join('');
    } else {
        alert('Failed to fetch user herbs: ' + data.error);
    }
}

// Fetch user's products (for sellers)
async function fetchUserProducts() {
    const { token } = checkAuth();
    const response = await fetch('/api/user/products', {
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });
    const data = await response.json();

    if (response.ok) {
        const userProductsContainer = document.getElementById('user-products');
        userProductsContainer.innerHTML = data.products.map(product => `
            <div class="mb-3">
                <h5>${product.name}</h5>
                <p><strong>Price:</strong> $${product.price}</p>
                <p><strong>Stock:</strong> ${product.stock}</p>
            </div>
        `).join('');
    } else {
        alert('Failed to fetch user products: ' + data.error);
    }
}

// Function to toggle dark mode
function toggleDarkMode() {
    const body = document.body;
    body.classList.toggle('dark-mode');
    localStorage.setItem('dark-mode', body.classList.contains('dark-mode'));
}

// Initialize dark mode based on user preference
function initializeDarkMode() {
    const isDarkMode = localStorage.getItem('dark-mode') === 'true';
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
    }
}

// Initialize dark mode on page load
initializeDarkMode();

// Add event listener for dark mode toggle button
const darkModeToggle = document.getElementById('dark-mode-toggle');
if (darkModeToggle) {
    darkModeToggle.addEventListener('click', toggleDarkMode);
}