FROM node:slim

# Create the application directory
RUN mkdir /tokenizer

# Create the working environment
RUN mkdir -p /tokenizer/src /tokenizer/config
WORKDIR "/tokenizer"

# Deploy code
COPY package*.json /tokenizer/
COPY src/* /tokenizer/src/
COPY config/* /tokenizer/config/

RUN npm install
CMD [ "npm", "start" ]
