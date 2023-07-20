### STAGE 1: Installing and building the angular application ###
FROM node:18.12-alpine AS builder

WORKDIR /app

COPY / ./
COPY package*.json ./

ENV GATEWAY_URL=$GATEWAY_URL

RUN npm install -g @angular/cli@15.2.4 && \
    npm install && \
    ng build

#COPY . .

### STAGE 2: Copy the angular dist folder from the build to the nginx location folder ###
FROM nginx:stable-alpine3.17

# copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
# copy artifact build from the 'build environment'
COPY --from=builder /app/dist/sample-angular-app /usr/share/nginx/html

EXPOSE 8080
#
# run nginx
CMD ["nginx", "-g", "daemon off;"]
