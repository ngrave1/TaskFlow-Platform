CREATE DATABASE user_service;
CREATE DATABASE task_service;
CREATE DATABASE notification_service;
CREATE DATABASE analytics_service;

GRANT ALL PRIVILEGES ON DATABASE user_service TO admin;
GRANT ALL PRIVILEGES ON DATABASE task_service TO admin;
GRANT ALL PRIVILEGES ON DATABASE notification_service TO admin;
GRANT ALL PRIVILEGES ON DATABASE analytics_service TO admin;