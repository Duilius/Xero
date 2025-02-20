// session_manager.js
class SessionManager {
    constructor() {
        this.inactivityTimeout = 25 * 60 * 1000; // 25 minutos
        this.warningTimeout = 28 * 60 * 1000;    // 28 minutos
        this.maxTimeout = 30 * 60 * 1000;        // 30 minutos
        this.initializeTimers();
        this.setupEventListeners();
    }

    initializeTimers() {
        this.lastActivity = Date.now();
        this.checkInterval = setInterval(() => this.checkSession(), 1000);
    }

    resetTimer() {
        this.lastActivity = Date.now();
        if (this.warningShown) {
            this.hideWarning();
        }
    }

    async checkSession() {
        const inactiveTime = Date.now() - this.lastActivity;

        if (inactiveTime >= this.maxTimeout) {
            await this.handleSessionExpired();
        } else if (inactiveTime >= this.warningTimeout && !this.warningShown) {
            this.showWarning();
        }
    }

    showWarning() {
        if (this.warningShown) return;

        const warningModal = document.createElement('div');
        warningModal.innerHTML = `
            <div class="fixed inset-0 bg-gray-600 bg-opacity-50 z-50 flex items-center justify-center">
                <div class="bg-white p-6 rounded-lg shadow-xl max-w-md w-full mx-4">
                    <h3 class="text-lg font-semibold mb-4">Session Warning</h3>
                    <p class="mb-4">Your session will expire in 2 minutes.</p>
                    <div class="flex justify-end space-x-4">
                        <button id="end-session" class="px-4 py-2 border text-gray-600 rounded hover:bg-gray-100">
                            End Session
                        </button>
                        <button id="refresh-session" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                            Continue Working
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(warningModal);
        this.warningShown = true;

        document.getElementById('refresh-session').onclick = async () => {
            await this.refreshSession();
            warningModal.remove();
            this.warningShown = false;
        };

        document.getElementById('end-session').onclick = async () => {
            try {
                // Llamar al endpoint de logout
                const response = await fetch('/auth/logout', {
                    method: 'POST',
                    credentials: 'include'
                });
                
                // Limpiar storage
                sessionStorage.clear();
                
                // La redirección la maneja el backend
            } catch (error) {
                console.error('Error ending session:', error);
                window.location.href = '/';
            }
        };
    }

    async refreshSession() {
        try {
            console.log('Starting session refresh');
            const response = await fetch('/auth/refresh', {
                method: 'POST',
                credentials: 'include'
            });
    
            console.log('Refresh response status:', response.status);
            if (!response.ok) {
                throw new Error('Session refresh failed');
            }
    
            console.log('Session refreshed successfully');
            this.resetTimer();
        } catch (error) {
            console.error('Session refresh error:', error);
            await this.handleSessionExpired();
        }
    }

    async handleSessionExpired() {
        clearInterval(this.checkInterval);
        const response = await fetch('/auth/login-redirect');
        if (response.ok) {
            const { url } = await response.json();
            window.location.href = url;
        }
    }

    setupEventListeners() {
        ['mousemove', 'keypress', 'scroll', 'click'].forEach(event => {
            window.addEventListener(event, () => this.resetTimer());
        });
    }
}

// Al final del archivo session_manager.js
const sessionManager = new SessionManager();