-- Initial Database Setup for Financial Analytics Platform
-- This script creates the database schema and populates it with sample data

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create organizations table
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    website VARCHAR(255),
    industry VARCHAR(100),
    size VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role VARCHAR(50) DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    phone VARCHAR(20),
    timezone VARCHAR(50) DEFAULT 'UTC',
    preferences JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    organization_id UUID NOT NULL REFERENCES organizations(id),
    hashed_password VARCHAR(255) NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Create user_permissions table
CREATE TABLE IF NOT EXISTS user_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    permission VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    granted_by UUID NOT NULL REFERENCES users(id),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Create accounts table
CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    account_type VARCHAR(100) NOT NULL,
    institution VARCHAR(255) NOT NULL,
    account_number VARCHAR(100),
    routing_number VARCHAR(100),
    currency VARCHAR(3) DEFAULT 'USD',
    balance DECIMAL(15,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    organization_id UUID NOT NULL REFERENCES organizations(id),
    owner_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Create categories table
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    color VARCHAR(7),
    icon VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    organization_id UUID NOT NULL REFERENCES organizations(id),
    owner_id UUID NOT NULL REFERENCES users(id),
    parent_id UUID REFERENCES categories(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Create transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    amount DECIMAL(15,2) NOT NULL,
    description VARCHAR(1000) NOT NULL,
    transaction_type VARCHAR(100) NOT NULL,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    reference VARCHAR(255),
    notes TEXT,
    is_recurring BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    organization_id UUID NOT NULL REFERENCES organizations(id),
    user_id UUID NOT NULL REFERENCES users(id),
    account_id UUID NOT NULL REFERENCES accounts(id),
    category_id UUID REFERENCES categories(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Create budgets table
CREATE TABLE IF NOT EXISTS budgets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    amount DECIMAL(15,2) NOT NULL,
    period VARCHAR(50) NOT NULL,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    organization_id UUID NOT NULL REFERENCES organizations(id),
    owner_id UUID NOT NULL REFERENCES users(id),
    category_id UUID REFERENCES categories(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT TRUE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_organization_id ON users(organization_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_accounts_organization_id ON accounts(organization_id);
CREATE INDEX IF NOT EXISTS idx_accounts_owner_id ON accounts(owner_id);
CREATE INDEX IF NOT EXISTS idx_categories_organization_id ON categories(organization_id);
CREATE INDEX IF NOT EXISTS idx_categories_parent_id ON categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_transactions_organization_id ON transactions(organization_id);
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_account_id ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_category_id ON transactions(category_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_budgets_organization_id ON budgets(organization_id);
CREATE INDEX IF NOT EXISTS idx_budgets_owner_id ON budgets(owner_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_organization_id ON audit_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_accounts_updated_at BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_budgets_updated_at BEFORE UPDATE ON budgets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data

-- Sample Organizations
INSERT INTO organizations (name, slug, description, website, industry, size, metadata) VALUES
('Acme Corporation', 'acme-corp', 'A leading technology company specializing in innovative solutions', 'https://acme-corp.com', 'Technology', 'Enterprise', '{"founded": "1995", "headquarters": "San Francisco, CA"}'),
('Global Finance Group', 'global-finance', 'International financial services and investment management', 'https://globalfinance.com', 'Financial Services', 'Large', '{"founded": "1980", "headquarters": "New York, NY"}'),
('Startup Ventures', 'startup-ventures', 'Early-stage startup incubator and venture capital firm', 'https://startupventures.com', 'Venture Capital', 'Small', '{"founded": "2010", "headquarters": "Austin, TX"}'),
('Local Community Bank', 'local-bank', 'Community-focused banking services for local residents and businesses', 'https://localbank.com', 'Banking', 'Medium', '{"founded": "1975", "headquarters": "Chicago, IL"}'),
('Green Energy Co', 'green-energy', 'Renewable energy solutions and sustainable technology', 'https://greenenergy.com', 'Energy', 'Medium', '{"founded": "2005", "headquarters": "Denver, CO"}');

-- Sample Users (passwords are hashed versions of 'password123')
INSERT INTO users (email, first_name, last_name, role, organization_id, hashed_password, is_verified) VALUES
('admin@acme-corp.com', 'John', 'Admin', 'admin', (SELECT id FROM organizations WHERE slug = 'acme-corp'), '$argon2id$v=19$m=65536,t=3,p=4$hash_placeholder', TRUE),
('analyst@acme-corp.com', 'Sarah', 'Analyst', 'analyst', (SELECT id FROM organizations WHERE slug = 'acme-corp'), '$argon2id$v=19$m=65536,t=3,p=4$hash_placeholder', TRUE),
('viewer@acme-corp.com', 'Mike', 'Viewer', 'viewer', (SELECT id FROM organizations WHERE slug = 'acme-corp'), '$argon2id$v=19$m=65536,t=3,p=4$hash_placeholder', TRUE),
('admin@global-finance.com', 'Lisa', 'Manager', 'admin', (SELECT id FROM organizations WHERE slug = 'global-finance'), '$argon2id$v=19$m=65536,t=3,p=4$hash_placeholder', TRUE),
('analyst@global-finance.com', 'David', 'Financial', 'analyst', (SELECT id FROM organizations WHERE slug = 'global-finance'), '$argon2id$v=19$m=65536,t=3,p=4$hash_placeholder', TRUE),
('admin@startup-ventures.com', 'Alex', 'Founder', 'admin', (SELECT id FROM organizations WHERE slug = 'startup-ventures'), '$argon2id$v=19$m=65536,t=3,p=4$hash_placeholder', TRUE),
('admin@local-bank.com', 'Maria', 'Banker', 'admin', (SELECT id FROM organizations WHERE slug = 'local-bank'), '$argon2id$v=19$m=65536,t=3,p=4$hash_placeholder', TRUE),
('admin@green-energy.com', 'Tom', 'Green', 'admin', (SELECT id FROM organizations WHERE slug = 'green-energy'), '$argon2id$v=19$m=65536,t=3,p=4$hash_placeholder', TRUE);

-- Sample Categories
INSERT INTO categories (name, description, color, icon, organization_id, owner_id) VALUES
('Food & Dining', 'Restaurants, groceries, and dining expenses', '#FF6B6B', '🍽️', (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com')),
('Transportation', 'Gas, public transit, and vehicle expenses', '#4ECDC4', '🚗', (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com')),
('Entertainment', 'Movies, games, and leisure activities', '#45B7D1', '🎬', (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com')),
('Shopping', 'Clothing, electronics, and retail purchases', '#96CEB4', '🛍️', (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com')),
('Utilities', 'Electricity, water, and internet bills', '#FFEAA7', '💡', (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com')),
('Healthcare', 'Medical expenses and insurance', '#DDA0DD', '🏥', (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com')),
('Income', 'Salary, bonuses, and other income sources', '#98D8C8', '💰', (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com')),
('Investment', 'Stock purchases, dividends, and investment returns', '#F7DC6F', '📈', (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com'));

-- Sample Accounts
INSERT INTO accounts (name, account_type, institution, account_number, currency, balance, organization_id, owner_id) VALUES
('Main Checking', 'checking', 'Chase Bank', '****1234', 'USD', 5420.50, (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com')),
('Savings Account', 'savings', 'Chase Bank', '****5678', 'USD', 15750.00, (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com')),
('Credit Card', 'credit', 'American Express', '****9012', 'USD', -1250.75, (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com')),
('Investment Portfolio', 'investment', 'Fidelity', '****3456', 'USD', 45000.00, (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com')),
('Business Account', 'business', 'Wells Fargo', '****7890', 'USD', 8750.25, (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com'));

-- Sample Transactions
INSERT INTO transactions (amount, description, transaction_type, date, reference, category_id, organization_id, user_id, account_id) VALUES
(-45.67, 'Lunch at Chipotle', 'expense', '2024-01-15 12:30:00', 'CHIP123', (SELECT id FROM categories WHERE name = 'Food & Dining'), (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com'), (SELECT id FROM accounts WHERE name = 'Main Checking')),
(-32.50, 'Gas station fill-up', 'expense', '2024-01-15 08:15:00', 'SHEL456', (SELECT id FROM categories WHERE name = 'Transportation'), (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com'), (SELECT id FROM accounts WHERE name = 'Main Checking')),
(-89.99, 'Amazon Prime subscription', 'expense', '2024-01-14 15:20:00', 'AMZN789', (SELECT id FROM categories WHERE name = 'Shopping'), (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com'), (SELECT id FROM accounts WHERE name = 'Credit Card')),
(-156.78, 'Electricity bill', 'expense', '2024-01-13 10:00:00', 'PGE012', (SELECT id FROM categories WHERE name = 'Utilities'), (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com'), (SELECT id FROM accounts WHERE name = 'Main Checking')),
(5000.00, 'Salary deposit', 'income', '2024-01-15 09:00:00', 'SALARY001', (SELECT id FROM categories WHERE name = 'Income'), (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com'), (SELECT id FROM accounts WHERE name = 'Main Checking')),
(-67.89, 'Grocery shopping at Safeway', 'expense', '2024-01-12 16:45:00', 'SAFE345', (SELECT id FROM categories WHERE name = 'Food & Dining'), (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com'), (SELECT id FROM accounts WHERE name = 'Main Checking')),
(-24.99, 'Netflix subscription', 'expense', '2024-01-11 14:30:00', 'NETF678', (SELECT id FROM categories WHERE name = 'Entertainment'), (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com'), (SELECT id FROM accounts WHERE name = 'Credit Card')),
(-125.00, 'Doctor visit copay', 'expense', '2024-01-10 11:15:00', 'DOC901', (SELECT id FROM categories WHERE name = 'Healthcare'), (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com'), (SELECT id FROM accounts WHERE name = 'Main Checking')),
(250.00, 'Dividend payment', 'income', '2024-01-09 13:00:00', 'DIV234', (SELECT id FROM categories WHERE name = 'Investment'), (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com'), (SELECT id FROM accounts WHERE name = 'Investment Portfolio')),
(-89.50, 'Dinner at Italian restaurant', 'expense', '2024-01-08 19:30:00', 'ITAL567', (SELECT id FROM categories WHERE name = 'Food & Dining'), (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com'), (SELECT id FROM accounts WHERE name = 'Credit Card'));

-- Sample Budgets
INSERT INTO budgets (name, description, amount, period, start_date, end_date, organization_id, owner_id, category_id) VALUES
('Monthly Food Budget', 'Budget for all food and dining expenses', 800.00, 'monthly', '2024-01-01 00:00:00', '2024-01-31 23:59:59', (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com'), (SELECT id FROM categories WHERE name = 'Food & Dining')),
('Transportation Budget', 'Monthly budget for gas and transit', 300.00, 'monthly', '2024-01-01 00:00:00', '2024-01-31 23:59:59', (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com'), (SELECT id FROM categories WHERE name = 'Transportation')),
('Entertainment Budget', 'Monthly budget for entertainment and leisure', 200.00, 'monthly', '2024-01-01 00:00:00', '2024-01-31 23:59:59', (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com'), (SELECT id FROM categories WHERE name = 'Entertainment')),
('Shopping Budget', 'Monthly budget for retail purchases', 400.00, 'monthly', '2024-01-01 00:00:00', '2024-01-31 23:59:59', (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com'), (SELECT id FROM categories WHERE name = 'Shopping')),
('Annual Savings Goal', 'Yearly savings target', 12000.00, 'yearly', '2024-01-01 00:00:00', '2024-12-31 23:59:59', (SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com'), NULL);

-- Sample Audit Logs
INSERT INTO audit_logs (organization_id, user_id, action, resource_type, resource_id, details, ip_address, user_agent, success) VALUES
((SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com'), 'user_login', 'auth', NULL, '{"method": "password", "ip": "192.168.1.100"}', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', TRUE),
((SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com'), 'transaction_created', 'transaction', (SELECT id FROM transactions WHERE description = 'Lunch at Chipotle'), '{"amount": -45.67, "category": "Food & Dining"}', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', TRUE),
((SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'admin@acme-corp.com'), 'budget_created', 'budget', (SELECT id FROM budgets WHERE name = 'Monthly Food Budget'), '{"amount": 800.00, "period": "monthly"}', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', TRUE),
((SELECT id FROM organizations WHERE slug = 'acme-corp'), (SELECT id FROM users WHERE email = 'analyst@acme-corp.com'), 'user_login', 'auth', NULL, '{"method": "password", "ip": "192.168.1.101"}', '192.168.1.101', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36', TRUE),
((SELECT id FROM organizations WHERE slug = 'global-finance'), (SELECT id FROM users WHERE email = 'admin@global-finance.com'), 'user_login', 'auth', NULL, '{"method": "password", "ip": "192.168.1.102"}', '192.168.1.102', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36', TRUE);

-- Create views for common queries
CREATE OR REPLACE VIEW transaction_summary AS
SELECT 
    t.organization_id,
    t.category_id,
    c.name as category_name,
    c.color as category_color,
    COUNT(*) as transaction_count,
    SUM(CASE WHEN t.amount > 0 THEN t.amount ELSE 0 END) as total_income,
    SUM(CASE WHEN t.amount < 0 THEN ABS(t.amount) ELSE 0 END) as total_expenses,
    AVG(t.amount) as average_amount,
    MIN(t.date) as first_transaction,
    MAX(t.date) as last_transaction
FROM transactions t
LEFT JOIN categories c ON t.category_id = c.id
WHERE t.deleted_at IS NULL
GROUP BY t.organization_id, t.category_id, c.name, c.color;

CREATE OR REPLACE VIEW budget_vs_actual AS
SELECT 
    b.organization_id,
    b.id as budget_id,
    b.name as budget_name,
    b.amount as budget_amount,
    b.period as budget_period,
    COALESCE(SUM(CASE WHEN t.amount < 0 THEN ABS(t.amount) ELSE 0 END), 0) as actual_expenses,
    b.amount - COALESCE(SUM(CASE WHEN t.amount < 0 THEN ABS(t.amount) ELSE 0 END), 0) as remaining_budget,
    CASE 
        WHEN b.amount > 0 THEN 
            (COALESCE(SUM(CASE WHEN t.amount < 0 THEN ABS(t.amount) ELSE 0 END), 0) / b.amount) * 100
        ELSE 0 
    END as budget_usage_percentage
FROM budgets b
LEFT JOIN transactions t ON b.organization_id = t.organization_id 
    AND b.category_id = t.category_id 
    AND t.date BETWEEN b.start_date AND b.end_date
    AND t.deleted_at IS NULL
WHERE b.deleted_at IS NULL
GROUP BY b.id, b.organization_id, b.name, b.amount, b.period;

-- Grant permissions (adjust as needed for your security requirements)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO finance_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO finance_user;

-- Create a function to get financial summary
CREATE OR REPLACE FUNCTION get_financial_summary(org_id UUID, start_date TIMESTAMP, end_date TIMESTAMP)
RETURNS TABLE (
    total_income DECIMAL(15,2),
    total_expenses DECIMAL(15,2),
    net_amount DECIMAL(15,2),
    transaction_count BIGINT,
    avg_transaction DECIMAL(15,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(SUM(CASE WHEN t.amount > 0 THEN t.amount ELSE 0 END), 0) as total_income,
        COALESCE(SUM(CASE WHEN t.amount < 0 THEN ABS(t.amount) ELSE 0 END), 0) as total_expenses,
        COALESCE(SUM(t.amount), 0) as net_amount,
        COUNT(*) as transaction_count,
        COALESCE(AVG(t.amount), 0) as avg_transaction
    FROM transactions t
    WHERE t.organization_id = org_id
        AND t.date BETWEEN start_date AND end_date
        AND t.deleted_at IS NULL;
END;
$$ LANGUAGE plpgsql;

-- Create a function to get category breakdown
CREATE OR REPLACE FUNCTION get_category_breakdown(org_id UUID, start_date TIMESTAMP, end_date TIMESTAMP)
RETURNS TABLE (
    category_name VARCHAR(255),
    category_color VARCHAR(7),
    transaction_count BIGINT,
    total_amount DECIMAL(15,2),
    percentage DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.name as category_name,
        c.color as category_color,
        COUNT(*) as transaction_count,
        SUM(t.amount) as total_amount,
        CASE 
            WHEN SUM(CASE WHEN t.amount < 0 THEN ABS(t.amount) ELSE 0 END) > 0 THEN
                (SUM(CASE WHEN t.amount < 0 THEN ABS(t.amount) ELSE 0 END) / 
                 (SELECT COALESCE(SUM(CASE WHEN t2.amount < 0 THEN ABS(t2.amount) ELSE 0 END), 1)
                  FROM transactions t2 
                  WHERE t2.organization_id = org_id 
                    AND t2.date BETWEEN start_date AND end_date 
                    AND t2.deleted_at IS NULL)) * 100
            ELSE 0 
        END as percentage
    FROM transactions t
    LEFT JOIN categories c ON t.category_id = c.id
    WHERE t.organization_id = org_id
        AND t.date BETWEEN start_date AND end_date
        AND t.deleted_at IS NULL
    GROUP BY c.id, c.name, c.color
    ORDER BY total_amount DESC;
END;
$$ LANGUAGE plpgsql;

-- Insert additional sample data for other organizations
INSERT INTO categories (name, description, color, icon, organization_id, owner_id) VALUES
('Trading', 'Stock trading and investment activities', '#FF6B6B', '📊', (SELECT id FROM organizations WHERE slug = 'global-finance'), (SELECT id FROM users WHERE email = 'admin@global-finance.com')),
('Client Services', 'Client-related expenses and services', '#4ECDC4', '👥', (SELECT id FROM organizations WHERE slug = 'global-finance'), (SELECT id FROM users WHERE email = 'admin@global-finance.com')),
('Office Expenses', 'Office supplies and operational costs', '#45B7D1', '🏢', (SELECT id FROM organizations WHERE slug = 'global-finance'), (SELECT id FROM users WHERE email = 'admin@global-finance.com'));

INSERT INTO accounts (name, account_type, institution, account_number, currency, balance, organization_id, owner_id) VALUES
('Trading Account', 'investment', 'E*TRADE', '****1111', 'USD', 125000.00, (SELECT id FROM organizations WHERE slug = 'global-finance'), (SELECT id FROM users WHERE email = 'admin@global-finance.com')),
('Business Checking', 'checking', 'Chase Bank', '****2222', 'USD', 45000.00, (SELECT id FROM organizations WHERE slug = 'global-finance'), (SELECT id FROM users WHERE email = 'admin@global-finance.com')),
('Client Escrow', 'escrow', 'Wells Fargo', '****3333', 'USD', 250000.00, (SELECT id FROM organizations WHERE slug = 'global-finance'), (SELECT id FROM users WHERE email = 'admin@global-finance.com'));

-- Final message
SELECT 'Database initialization completed successfully!' as status;