FROM node:22-alpine

WORKDIR /app

# 配置 npm 国内镜像
RUN npm config set registry https://registry.npmmirror.com

COPY package.json ./
# 删除 Windows 生成的 lockfile，让 Linux 环境重新解析
RUN rm -f package-lock.json && npm install

COPY . .

RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
