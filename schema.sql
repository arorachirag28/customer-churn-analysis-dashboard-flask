CREATE DATABASE IF NOT EXISTS churn_analytics;
USE churn_analytics;

CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    customer_name VARCHAR(120) NOT NULL,
    email VARCHAR(160) NOT NULL,
    city VARCHAR(80) NOT NULL,
    state VARCHAR(80) NOT NULL,
    operator VARCHAR(40) NOT NULL,
    plan_type VARCHAR(40) NOT NULL,
    segment VARCHAR(40) NOT NULL,
    contract_type VARCHAR(40) NOT NULL,
    tenure_months INT NOT NULL,
    monthly_revenue DECIMAL(12,2) NOT NULL,
    usage_change_pct DECIMAL(6,2) NOT NULL,
    support_tickets INT NOT NULL DEFAULT 0,
    nps_score INT NOT NULL,
    payment_failures INT NOT NULL DEFAULT 0,
    last_login_days INT NOT NULL,
    churned BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO customers
(customer_id, customer_name, email, city, state, operator, plan_type, segment, contract_type, tenure_months, monthly_revenue, usage_change_pct, support_tickets, nps_score, payment_failures, last_login_days, churned)
VALUES
('IND-1001','Aarav Sharma','ind1001@example.in','Mumbai','Maharashtra','Jio','Postpaid','Metro','Month-to-month',14,1299,-42,2,5,1,22,1),
('IND-1002','Priya Nair','ind1002@example.in','Kochi','Kerala','Airtel','Broadband','Urban','Annual',31,1599,6,0,8,0,3,0),
('IND-1003','Rohan Mehta','ind1003@example.in','Ahmedabad','Gujarat','Vi','Prepaid','Semi-urban','Month-to-month',8,499,-28,1,6,1,15,0),
('IND-1004','Sneha Iyer','ind1004@example.in','Chennai','Tamil Nadu','Jio','Family Plan','Metro','Annual',46,2199,4,0,9,0,2,0),
('IND-1005','Arjun Reddy','ind1005@example.in','Hyderabad','Telangana','Airtel','Postpaid','Urban','Month-to-month',11,999,-51,3,4,1,29,1)
ON DUPLICATE KEY UPDATE customer_name = VALUES(customer_name);
