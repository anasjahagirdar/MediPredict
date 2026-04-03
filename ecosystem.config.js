/**
 * Azure Deployment Cheat Sheet
 *
 * 1. sudo apt update && sudo apt install -y python3-pip python3-venv nginx
 * 2. sudo npm install -g pm2 serve
 * 3. cd /path/to/MediPredict_Project/backend
 * 4. python3 -m venv venv
 * 5. source venv/bin/activate
 * 6. pip install -r requirements.txt
 * 7. cd ../frontend
 * 8. npm install
 * 9. npm run build
 * 10. cd ..
 * 11. pm2 start ecosystem.config.js
 * 12. pm2 save
 * 13. pm2 startup
 */

module.exports = {
  apps: [
    {
      name: 'medipredict-api',
      cwd: './backend',
      script: 'gunicorn',
      args: 'health_project.wsgi:application --bind 0.0.0.0:8000 --workers 3',
      interpreter: 'none',
      env: {
        DJANGO_SECRET_KEY: 'replace-with-production-secret',
        DJANGO_DEBUG: 'False',
        DJANGO_ALLOWED_HOSTS: 'your-api-domain,127.0.0.1,localhost',
        DB_MODE: 'cloud',
        DB_NAME: 'replace-with-azure-sql-db-name',
        DB_USER: 'replace-with-azure-sql-user',
        DB_PASSWORD: 'replace-with-azure-sql-password',
        DB_HOST: 'replace-with-azure-sql-host',
        DB_PORT: '1433',
        DB_DRIVER: 'ODBC Driver 18 for SQL Server',
        FRONTEND_PRODUCTION_ORIGIN: 'https://your-frontend-domain',
      },
    },
    {
      name: 'medipredict-ui',
      cwd: './frontend',
      script: 'serve',
      args: '-s dist -l 3000',
      interpreter: 'none',
      env: {
        NODE_ENV: 'production',
      },
    },
  ],
};
