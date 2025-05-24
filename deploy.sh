#!/bin/bash

# 检查域名解析
echo "Checking domain DNS..."
SERVER_IP=$(curl -s http://ipinfo.io/ip)
DOMAIN_IP=$(dig +short wvc.life)

if [ "$SERVER_IP" != "$DOMAIN_IP" ]; then
    echo "Warning: Domain wvc.life is not pointing to this server!"
    echo "Server IP: $SERVER_IP"
    echo "Domain IP: $DOMAIN_IP"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 停止现有服务
echo "Stopping existing services..."
sudo systemctl stop nginx
pkill -f uvicorn

# 创建必要的目录
echo "Creating directories..."
sudo mkdir -p /var/www/wvc.life
sudo mkdir -p /var/log/nginx
sudo mkdir -p /var/log/wvc.life

# 复制项目文件
echo "Copying project files..."
sudo cp -r ./* /var/www/wvc.life/
sudo chown -R www-data:www-data /var/www/wvc.life

# 安装依赖
echo "Installing dependencies..."
cd /var/www/wvc.life
pip3 install -r requirements.txt

# 检查Nginx配置
echo "Checking Nginx configuration..."
sudo nginx -t
if [ $? -ne 0 ]; then
    echo "Nginx configuration test failed!"
    exit 1
fi

# 启动FastAPI服务
echo "Starting FastAPI service..."
nohup python3 -m uvicorn vivogpt:app --host 127.0.0.1 --port 8000 > /var/log/wvc.life/fastapi.log 2>&1 &

# 等待FastAPI服务启动
echo "Waiting for FastAPI service to start..."
sleep 5

# 检查FastAPI服务
echo "Checking FastAPI service..."
if ! curl -s http://127.0.0.1:8000/api/query -I | grep "200\|404\|405" > /dev/null; then
    echo "FastAPI service is not responding!"
    exit 1
fi

# 启动Nginx
echo "Starting Nginx..."
sudo systemctl start nginx

# 检查Nginx服务
echo "Checking Nginx service..."
if ! systemctl is-active --quiet nginx; then
    echo "Nginx failed to start!"
    exit 1
fi

# 检查HTTPS访问
echo "Checking HTTPS access..."
if ! curl -sk https://wvc.life/api/query -I | grep "200\|404\|405" > /dev/null; then
    echo "HTTPS access is not working!"
    echo "Please check your SSL configuration and domain settings."
    exit 1
fi

echo "Deployment completed successfully!"
echo "You can now access your site at https://wvc.life"

# 显示服务状态
echo "Service Status:"
echo "---------------"
echo "FastAPI logs:"
tail -n 5 /var/log/wvc.life/fastapi.log
echo "---------------"
echo "Nginx error logs:"
tail -n 5 /var/log/nginx/wvc.life.error.log 