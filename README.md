# Gofind.ai Instagram API Project

The server will be taking the access token from and populate the database with search results. 
1. API call to get user name and store in the table
2. Another API call to get all recerent images.
3. The Json will be processed and all images will be stored in S3. 
A txt with all the image path will also be generated to be used in the YOLO script.
4. The YOLO script will take the txt and username and popurlate all the required fields 
inside the database. Segmented images will also be stored in S3.
