# Download base image ubuntu 22.04
FROM ubuntu:22.04

# LABEL about the custom image
LABEL maintainer="dancioc@nus.edu.sg"
LABEL version="0.1"
LABEL description="This is a custom Docker Image for Qiskit pQCee provider"

# Disable Prompt During Packages Installation
ARG DEBIAN_FRONTEND=noninteractive
# display
ENV DISPLAY=host.docker.internal:0.0
# timezone
ENV TZ=Asia/Singapore

# Update Ubuntu Software repository
# https://stackoverflow.com/questions/39760663/docker-ubuntu-bin-sh-1-locale-gen-not-found
# https://askubuntu.com/questions/162391/how-do-i-fix-my-locale-issue/229512#229512
RUN apt-get update && apt upgrade -y && apt-get install -y locales && locale-gen "en_US.UTF-8" && dpkg-reconfigure locales

# add etherum ppa
RUN apt-get install -y software-properties-common && apt-get update && add-apt-repository ppa:ethereum/ethereum && apt-get update

# install necesary tools
RUN apt-get install curl sudo zip unzip git -y

# install python
RUN apt-get install python3 python3-pip -y

# install qiskit
RUN pip3 install qiskit[visualization]

# install sphinx
RUN apt-get install -y python3-sphinx
RUN pip3 install pydata_sphinx_theme && pip3 install sphinx-autodoc-typehints && pip3 install sphinx-autoapi && pip3 install sphinxcontrib-autoprogram

# install solidity
RUN apt-get install -y solc

# install web3/pyevm ... and py-solc-x
RUN pip3 install web3[tester] && pip install py-solc-x

# for uploading packages
RUN pip3 install twine