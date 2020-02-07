# Catlog Application program

This is a catalog application that provides a list of items within a variety of categories.

# Prerequisites

To run this project, you'll need a Linux virtual machine, This will give you the support software needed for this project.

1. Installing the Virtual Machine

[VirtualBox](https://www.virtualbox.org/wiki/Download_Old_Builds_5_1) to install and manage the VM.

2. Install Vagrant :

[Vagrant](https://www.vagrantup.com) 
Vagrant is the software that configures the VM and lets you share files between your host computer and the VM's filesystem.Install the version for your operating system.

3. Download the VM configuration :

You can download and unzip this file: [fullstack-nanodegree-vm-master.zip](https://github.com/udacity/fullstack-nanodegree-vm) This will give you a virtual machien that contain libraries needed to run this project.

you will end up with a new directory containing the VM files. Change to this directory in your terminal with `cd`
Inside, you will find another directory called **vagrant**
Change directory to the vagrant directory:
![](https://video.udacity-data.com/topher/2016/December/58487f12_screen-shot-2016-12-07-at-13.28.31/screen-shot-2016-12-07-at-13.28.31.png)

4. copy the file named **cataloge** and put it inside **vagrant** directory.

5. Start the virtual machine:

From your terminal, inside the vagrant subdirectory, run the command `vagrant up`. This will cause Vagrant to download the Linux operating system and install it.
![](https://video.udacity-data.com/topher/2016/December/58488603_screen-shot-2016-12-07-at-13.57.50/screen-shot-2016-12-07-at-13.57.50.png)

When vagrant up is finished running, you will get your shell prompt back. At this point, you can run `vagrant ssh` to log in to your newly installed Linux VM
![](https://video.udacity-data.com/topher/2016/December/58488962_screen-shot-2016-12-07-at-14.12.29/screen-shot-2016-12-07-at-14.12.29.png)

Inside the VM, change directory to **/vagrant**.

## Getting results from the program

1. from your vm `cd` to **vagrant** directory then type the  command `python catalog/application.py`

2. Access THE application by visiting : http://localhost:8000 locally.

3. The application provides a JSON endpoint at: /catalog.json/


## NOTE: Styling this project was based on udacity's style sheet for some examples.

## Author

sajed tareq
