#!/bin/bash
ZONE="us-west3-a"
MACHINE="e2-micro"
IMAGE_FAMILY="debian-12"
IMAGE_PROJECT="debian-cloud"

# # Create 5 products RPC nodes
for i in 0 1 2 3 4; do
  gcloud compute instances create products-rpc-$i \
    --zone=$ZONE \
    --machine-type=$MACHINE \
    --image-family=$IMAGE_FAMILY \
    --image-project=$IMAGE_PROJECT \
    --boot-disk-size=10GB \
    --no-address \
    --tags=rpc-node
done

# Create 5 customers RPC nodes
for i in 0 1 2 3 4; do
  gcloud compute instances create customers-rpc-$i \
    --zone=$ZONE \
    --machine-type=$MACHINE \
    --image-family=$IMAGE_FAMILY \
    --image-project=$IMAGE_PROJECT \
    --boot-disk-size=10GB \
    --no-address \
    --tags=rpc-node
done

# Create 1 customer frontend server
gcloud compute instances create customer-frontend \
  --zone=$ZONE \
  --machine-type=$MACHINE \
  --image-family=$IMAGE_FAMILY \
  --image-project=$IMAGE_PROJECT \
  --boot-disk-size=10GB \
  --tags=frontend

# Create 1 seller frontend server
gcloud compute instances create seller-frontend \
  --zone=$ZONE \
  --machine-type=$MACHINE \
  --image-family=$IMAGE_FAMILY \
  --image-project=$IMAGE_PROJECT \
  --boot-disk-size=10GB \
  --tags=frontend

# Create 1 payment API server
gcloud compute instances create payment-api \
  --zone=$ZONE \
  --machine-type=$MACHINE \
  --image-family=$IMAGE_FAMILY \
  --image-project=$IMAGE_PROJECT \
  --boot-disk-size=10GB \
  --tags=api


gcloud compute routers create nat-router \
  --project=distributed-systems-487323 \
  --network=default \
  --region=us-west3

gcloud compute routers nats create nat-gateway \
  --project=distributed-systems-487323 \
  --router=nat-router \
  --region=us-west3 \
  --auto-allocate-nat-external-ips \
  --nat-all-subnet-ip-ranges