Introduction  
    This course gave us a brief view of artificial intelligence. We have learned multiple classic models and concepts on how to apply these models on real-life problems. After delving into the domain of AI, we determined to participate in the IJCAI competition to demonstrate our achievement and have further insight in the field of AI.
    In this challenge, our mission is to forecast future strokes including shot types and locations given the past stroke sequences. For each singles rally, given the observed 4 strokes with type-area pairs and two players, the goal is to predict the future strokes including shot types and area coordinates for the next n steps. n is various based on the length of the rally.

Prerequest  
    This code can be conduct in a colab environment, up load the CoachAI-Project-main folder to google drive and conduct following code:
    from google.colab import drive
    from google.colab.patches import cv2_imshow
    drive.mount('/content/gdrive')
    %cd /content
    !unzip /content/gdrive/MyDrive/CoachAI-Projects-main.zip  
    %cd /content/CoachAI-Projects-main/CoachAI-Projects-main/CoachAI-Challenge-IJCAI2023/Track 2_ Stroke Forecasting/src
    !sh script.sh
    !python generator.py {model direction}
   
Method  
    We mainly change the number of epoch in training, we use curve fitting and try and error method to find the best epoch number.
