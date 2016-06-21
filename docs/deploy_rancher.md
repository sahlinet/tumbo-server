# Deploy Tumbo on Rancher

## Environment Configuration

Create a file `your-env.env` with following environment variables:

    PASSWORD                 
    RABBITMQ_PASS
    REDIS_PASS
    ADMIN_PASSWORD
    ALLOWED_HOSTS

    RANCHER_ACCESS_KEY
    RANCHER_ACCESS_SECRET
    RANCHER_ENVIRONMENT_ID
    RANCHER_URL

    FRONTEND_HOST

    DEBUG

# Run on Rancher

    wget https://releases.rancher.com/compose/beta/v0.7.2/rancher-compose-linux-amd64-v0.7.2.tar.gz
    tar -zxvf rancher-compose-linux-amd64-v0.7.2.tar.gz                                                                                                                 
    sudo mv rancher-compose-v0.7.2/rancher-compose  /usr/local/bin 
    rm -rf rancher-compose-v0*
    
    export RANCHER_ACCESS_KEY=ACCESS_KEY                                                                                                                      
    export RANCHER_SECRET_KEY=SECRET_KEY                                                                                       
    export RANCHER_URL=http://URL
    
    rancher-compose -p tumbo -f docker-compose.yml -e your-env.env  up