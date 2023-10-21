# Computer-Vision-System
Allow me to introduce Project Hawkeye, a computer vision quality assurance tool that tracks quality metrics in real
time to improve processes, increase customer satisfaction, and reduce waste for production processes
worldwide. The project is based on groundbreaking technology advancements made in the last 10 years
that allow us to retrieve information about our product from a video film in real time.
When I was a process technician in a previous job, I remember how stressful and time consuming it was
to always be checking process lines for variations and defects. This was because every second a defect
was not caught resulted in another second of wasted product produced that would be scrapped or
repurposed. The solutions advertised in project Hawkeye offer real-time detection of this process,
saving money on operator time, equipment downtime, defective products, customer satisfaction and
much more!
Sources including AWS have confirmed that implementations of these “Computer-Vision” systems have
reduced the quality defects produced on their production lines by around 50%. Based on conservative
estimates, we project that each vision system that we install will save Kingspan around $60,000 and just
over 2400 square meters of scrap per year.
I have attached a successful proof-of-concept vision system that displays a camera system that I had
built for a Kingspan PIR production line in Miami, Florida.

Below is an example of the application in use: 
https://github.com/mklimek25/Computer-Vision-System/assets/90988711/8f6055b4-a1f0-4d6f-ba86-4a8bc0baa41d

The outputs collected by the vision system can be used in a variety of ways. To make an immediate impact to operators, I created a GUI for operators to monitor product quality in real time. Below is an image of the GUI collected during production:
<img width="794" alt="CVS GUI" src="https://github.com/mklimek25/Computer-Vision-System/assets/90988711/a68f1117-10f7-4165-ac89-4951682ee506">

Every 5 seconds, the GUI is updated with the averge values of all collected ouputs. At the same time, a SQL database is populated with these average values that perform by actively while the vision system is reading data from frames.
