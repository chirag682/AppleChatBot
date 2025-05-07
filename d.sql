-- Drop the table if it exists
   DROP TABLE IF EXISTS hierarchy;
   DROP TABLE IF EXISTS annotations;


-- Create the hierarchy table
CREATE TABLE hierarchy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    l1 TEXT,
    l2 TEXT,
    l3 TEXT,
    is_leaf BOOLEAN,
    l4 TEXT NOT NULL DEFAULT 'ALL',
    l5 TEXT NOT NULL DEFAULT 'ALL',
    is_forecast BOOLEAN,
    group_id TEXT,
    description TEXT,
    is_not_deleted BOOLEAN DEFAULT TRUE,
    last_month_spending REAL,
    account_count_3pc INTEGER,
    account_count_first_party INTEGER,
    user_count INTEGER,
    domain_count_cdn INTEGER,
    last_month_cdn_spending REAL,
    CONSTRAINT hierarchy_unique UNIQUE (l1, l2, l3, l4, l5, is_not_deleted)
);

-- Create the annotations table
CREATE TABLE annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    email TEXT,
    timestamp DATETIME NOT NULL,
    content TEXT,
    hierarchy_id INTEGER,
    annotation_status TEXT DEFAULT 'COMPLETED',
    annotation_type TEXT CHECK(annotation_type IN ('monthly', 'yearly')) DEFAULT 'monthly',
    FOREIGN KEY (hierarchy_id) REFERENCES hierarchy (id) ON DELETE SET NULL
);

-- Create indexes for performance optimization
CREATE INDEX idx_hierarchy_l1_l2_l3 ON hierarchy (l1, l2, l3);
CREATE INDEX idx_annotations_hierarchy_id ON annotations (hierarchy_id);


-- Insert 25 dummy records into hierarchy table
INSERT INTO hierarchy (l1, l2, l3, is_leaf, l4, l5, is_forecast, group_id, description, is_not_deleted, last_month_spending, account_count_3pc, account_count_first_party, user_count, domain_count_cdn, last_month_cdn_spending)
VALUES
('Finance', 'Accounts', 'Payroll', TRUE, 'North America', 'ALL', FALSE, 'GRP001', 'Payroll department hierarchy', TRUE, 50000.75, 30, 15, 100, 5, 20000.50),
('Finance', 'Accounts', 'Taxes', TRUE, 'Europe', 'ALL', FALSE, 'GRP002', 'Tax department hierarchy', TRUE, 75000.25, 40, 20, 150, 10, 30000.75),
('IT', 'Infrastructure', 'Cloud Services', FALSE, 'Global', 'ALL', TRUE, 'GRP003', 'Cloud services hierarchy', TRUE, 100000.00, 50, 30, 200, 15, 50000.00),
('IT', 'Support', 'Helpdesk', TRUE, 'Asia', 'ALL', FALSE, 'GRP004', 'Helpdesk support hierarchy', TRUE, 20000.50, 20, 10, 80, 2, 5000.75),
('HR', 'Recruitment', 'Interviews', TRUE, 'US', 'ALL', FALSE, 'GRP005', 'Recruitment hierarchy', TRUE, 15000.25, 15, 7, 60, 1, 3000.50),
('Marketing', 'Advertising', 'Digital', TRUE, 'Europe', 'ALL', FALSE, 'GRP006', 'Digital marketing hierarchy', TRUE, 60000.00, 25, 15, 90, 4, 18000.75),
('Marketing', 'Advertising', 'Print', TRUE, 'US', 'ALL', FALSE, 'GRP007', 'Print advertising hierarchy', TRUE, 40000.00, 18, 10, 70, 3, 12000.00),
('Sales', 'Retail', 'Online', TRUE, 'Global', 'ALL', TRUE, 'GRP008', 'Online retail hierarchy', TRUE, 90000.00, 40, 25, 180, 8, 40000.50),
('Sales', 'Wholesale', 'Bulk', TRUE, 'North America', 'ALL', FALSE, 'GRP009', 'Bulk sales hierarchy', TRUE, 85000.00, 35, 20, 160, 6, 35000.75),
('Operations', 'Logistics', 'Shipping', TRUE, 'Global', 'ALL', FALSE, 'GRP010', 'Shipping and logistics hierarchy', TRUE, 70000.00, 30, 15, 140, 5, 25000.50),
('Operations', 'Logistics', 'Warehousing', TRUE, 'US', 'ALL', FALSE, 'GRP011', 'Warehousing hierarchy', TRUE, 55000.50, 28, 12, 110, 4, 18000.25),
('Finance', 'Investments', 'Stocks', TRUE, 'Europe', 'ALL', FALSE, 'GRP012', 'Stock investments hierarchy', TRUE, 120000.75, 60, 35, 250, 12, 60000.50),
('Finance', 'Investments', 'Bonds', TRUE, 'Asia', 'ALL', FALSE, 'GRP013', 'Bond investments hierarchy', TRUE, 95000.50, 55, 30, 220, 10, 50000.75),
('Legal', 'Compliance', 'Regulatory', TRUE, 'Global', 'ALL', TRUE, 'GRP014', 'Regulatory compliance hierarchy', TRUE, 30000.00, 18, 10, 85, 2, 8000.50),
('Legal', 'Contracts', 'Negotiations', TRUE, 'US', 'ALL', FALSE, 'GRP015', 'Contract negotiations hierarchy', TRUE, 28000.75, 15, 8, 75, 2, 7000.25),
('IT', 'Security', 'Cybersecurity', TRUE, 'Global', 'ALL', TRUE, 'GRP016', 'Cybersecurity hierarchy', TRUE, 150000.00, 80, 50, 300, 20, 90000.00),
('IT', 'Security', 'Data Protection', TRUE, 'Europe', 'ALL', FALSE, 'GRP017', 'Data protection hierarchy', TRUE, 130000.50, 75, 45, 280, 18, 75000.25),
('Research', 'Development', 'Product R&D', TRUE, 'North America', 'ALL', TRUE, 'GRP018', 'Product development hierarchy', TRUE, 110000.00, 65, 40, 230, 14, 65000.75),
('Research', 'Analysis', 'Market Trends', TRUE, 'Global', 'ALL', FALSE, 'GRP019', 'Market analysis hierarchy', TRUE, 98000.50, 58, 35, 210, 12, 50000.00),
('HR', 'Training', 'Employee Development', TRUE, 'US', 'ALL', FALSE, 'GRP020', 'Employee training hierarchy', TRUE, 45000.25, 25, 15, 100, 5, 15000.50),
('HR', 'Benefits', 'Healthcare', TRUE, 'Europe', 'ALL', FALSE, 'GRP021', 'Healthcare benefits hierarchy', TRUE, 75000.00, 38, 20, 130, 8, 28000.25),
('Operations', 'Manufacturing', 'Production', TRUE, 'Asia', 'ALL', TRUE, 'GRP022', 'Production hierarchy', TRUE, 125000.50, 70, 40, 260, 16, 70000.75),
('Operations', 'Manufacturing', 'Quality Control', TRUE, 'Global', 'ALL', FALSE, 'GRP023', 'Quality control hierarchy', TRUE, 88000.00, 48, 30, 190, 10, 45000.00),
('Sales', 'Customer Service', 'Support', TRUE, 'North America', 'ALL', FALSE, 'GRP024', 'Customer support hierarchy', TRUE, 68000.25, 33, 18, 140, 6, 25000.50),
('Sales', 'Customer Service', 'Retention', TRUE, 'US', 'ALL', FALSE, 'GRP025', 'Customer retention hierarchy', TRUE, 72000.50, 35, 20, 150, 7, 27000.25);

-- Insert 50 dummy records into annotations table
INSERT INTO annotations (username, email, timestamp, content, hierarchy_id, annotation_status, annotation_type)
VALUES
('user1', 'user1@example.com', DATETIME('now', '-1 days'), 'Forecast updated due to new sub-level addition.', 1, 'COMPLETED', 'monthly'),
('user2', 'user2@example.com', DATETIME('now', '-2 days'), 'Financial budget adjusted based on latest reports.', 2, 'PENDING', 'yearly'),
('user3', 'user3@example.com', DATETIME('now', '-3 days'), 'New sub-department added, affecting hierarchy structure.', 3, 'IN_PROGRESS', 'monthly'),
('user4', 'user4@example.com', DATETIME('now', '-4 days'), 'Revenue projection updated following market analysis.', 4, 'COMPLETED', 'yearly'),
('user5', 'user5@example.com', DATETIME('now', '-5 days'), 'Reorganization of teams resulted in changes to hierarchy.', 5, 'PENDING', 'monthly'),
('user6', 'user6@example.com', DATETIME('now', '-6 days'), 'Q1 financial report insights added to hierarchy overview.', 6, 'IN_PROGRESS', 'yearly'),
('user7', 'user7@example.com', DATETIME('now', '-7 days'), 'Structural realignment due to merging of two divisions.', 7, 'COMPLETED', 'monthly'),
('user8', 'user8@example.com', DATETIME('now', '-8 days'), 'Cost-cutting measures introduced, affecting forecasts.', 8, 'PENDING', 'yearly'),
('user9', 'user9@example.com', DATETIME('now', '-9 days'), 'New KPIs defined, impacting hierarchy evaluation metrics.', 9, 'IN_PROGRESS', 'monthly'),
('user10', 'user10@example.com', DATETIME('now', '-10 days'), 'Profit margin revision led to updates in financial model.', 10, 'COMPLETED', 'yearly'),
('user11', 'user11@example.com', DATETIME('now', '-11 days'), 'Sub-unit budget reallocated based on priority shifts.', 11, 'PENDING', 'monthly'),
('user12', 'user12@example.com', DATETIME('now', '-12 days'), 'Departmental split requires modifications to reporting structure.', 12, 'IN_PROGRESS', 'yearly'),
('user13', 'user13@example.com', DATETIME('now', '-13 days'), 'Revenue tracking mechanism updated for hierarchy consistency.', 13, 'COMPLETED', 'monthly'),
('user14', 'user14@example.com', DATETIME('now', '-14 days'), 'Expense categorization refined to improve financial accuracy.', 14, 'PENDING', 'yearly'),
('user15', 'user15@example.com', DATETIME('now', '-15 days'), 'Hierarchy adjusted due to executive role changes.', 15, 'IN_PROGRESS', 'monthly'),
('user16', 'user16@example.com', DATETIME('now', '-16 days'), 'New department added in response to business expansion.', 16, 'COMPLETED', 'yearly'),
('user17', 'user17@example.com', DATETIME('now', '-17 days'), 'Updated forecasting model to reflect recent economic trends.', 17, 'PENDING', 'monthly'),
('user18', 'user18@example.com', DATETIME('now', '-18 days'), 'Hierarchy restructuring following internal audit results.', 18, 'IN_PROGRESS', 'yearly'),
('user19', 'user19@example.com', DATETIME('now', '-19 days'), 'Financial review prompted redistribution of department budgets.', 19, 'COMPLETED', 'monthly'),
('user20', 'user20@example.com', DATETIME('now', '-20 days'), 'Cash flow statement revisions led to updated spending limits.', 20, 'PENDING', 'yearly'),
('user21', 'user21@example.com', DATETIME('now', '-21 days'), 'Performance review adjustments affected team structures.', 21, 'IN_PROGRESS', 'monthly'),
('user22', 'user22@example.com', DATETIME('now', '-22 days'), 'Investment reallocation requires hierarchy updates.', 22, 'COMPLETED', 'yearly'),
('user23', 'user23@example.com', DATETIME('now', '-23 days'), 'Market forecast adjustments changed regional allocations.', 23, 'PENDING', 'monthly'),
('user24', 'user24@example.com', DATETIME('now', '-24 days'), 'Department merger impact reflected in new hierarchy tree.', 24, 'IN_PROGRESS', 'yearly'),
('user25', 'user25@example.com', DATETIME('now', '-25 days'), 'Operational efficiency review resulted in structural changes.', 25, 'COMPLETED', 'monthly'),
('user26', 'user26@example.com', DATETIME('now', '-26 days'), 'Updated compliance guidelines affected financial projections.', 1, 'PENDING', 'yearly'),
('user27', 'user27@example.com', DATETIME('now', '-27 days'), 'Hierarchy adjustments made for better cross-team collaboration.', 2, 'IN_PROGRESS', 'monthly'),
('user28', 'user28@example.com', DATETIME('now', '-28 days'), 'Recent acquisitions led to hierarchy restructuring.', 3, 'COMPLETED', 'yearly'),
('user29', 'user29@example.com', DATETIME('now', '-29 days'), 'Revenue loss mitigation plan adjusted hierarchy nodes.', 4, 'PENDING', 'monthly'),
('user30', 'user30@example.com', DATETIME('now', '-30 days'), 'Budget approval process modifications impacted forecast.', 5, 'IN_PROGRESS', 'yearly'),
('user31', 'user31@example.com', DATETIME('now', '-31 days'), 'Leadership changes influenced department accountability.', 6, 'COMPLETED', 'monthly'),
('user32', 'user32@example.com', DATETIME('now', '-32 days'), 'New performance incentives introduced, affecting hierarchy.', 7, 'PENDING', 'yearly'),
('user33', 'user33@example.com', DATETIME('now', '-33 days'), 'Market expansion strategy required reorganization.', 8, 'IN_PROGRESS', 'monthly'),
('user34', 'user34@example.com', DATETIME('now', '-34 days'), 'Q3 forecast revisions implemented for accuracy.', 9, 'COMPLETED', 'yearly'),
('user35', 'user35@example.com', DATETIME('now', '-35 days'), 'Interdepartmental collaboration changes updated.', 10, 'PENDING', 'monthly'),
('user36', 'user36@example.com', DATETIME('now', '-36 days'), 'Cost-saving measures resulted in role adjustments.', 11, 'IN_PROGRESS', 'yearly'),
('user37', 'user37@example.com', DATETIME('now', '-37 days'), 'New sales projections influenced hierarchy decisions.', 12, 'COMPLETED', 'monthly'),
('user38', 'user38@example.com', DATETIME('now', '-38 days'), 'Revised market segmentation led to hierarchy tweaks.', 13, 'PENDING', 'yearly'),
('user39', 'user39@example.com', DATETIME('now', '-39 days'), 'Legal compliance updates impacted finance structure.', 14, 'IN_PROGRESS', 'monthly'),
('user40', 'user40@example.com', DATETIME('now', '-40 days'), 'Board recommendations led to new hierarchy rules.', 15, 'COMPLETED', 'yearly'),
('user41', 'user41@example.com', DATETIME('now', '-41 days'), 'Company growth forecasted, impacting team structures.', 16, 'PENDING', 'monthly'),
('user42', 'user42@example.com', DATETIME('now', '-42 days'), 'Project realignment changed resource distribution.', 17, 'IN_PROGRESS', 'yearly');


