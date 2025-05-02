# My Reflections and Outcomes of IS601 and this final project

## Overview

Throughout this class, I have learned a lot and genuinely things I didn't know about the computer science industry. My background before coming to NJIT was 3D animation and character effects, so I was kind of jumping in blind into this graduate program. Professor Williams genuinely made class interesting through his talks on modern day technology, AI, and what some jobs might be in the near future do to this shift in technology. I was so inspired to work on personal projects that I didn't think I could do before his class, and now I have a long term project in the works for helping animators in my industry. Of course this class was not only the in-person aspect, but I learned a lot more about how to code and to be in the mindset of a professional through his homeworks and video lectures. This was my first time being introduced to git, pytest, database management SQL like postgres, docker, setting up environment variables, and more importantly the basics of python coding. Before I started, I did a codecademy course on C++ since I know that it is one of the harder languages to learn and everything from that is easier. And well, I can definitely say Python is like pseudocode compared to C++ and it was super easy to catch on. Professor Williams also said AI mostly uses python for coding so I definitely want to explore more of that kind of code on my own time. And because of the skills I learned in this class, I am looking at job listings and actually understanding their requirements to be successful in that particular job when before I could't differentiate what git and github were (honestly thought they were the same thing, and I was sorely mistaken). But overall, this course taught me a lot to prepare for the real world and how to make yourself stand out on a portfolio from school using the logic and reasoning to solve the QA and technical problems of the code.

For this final project, I wanted to make sure github actions were working normally before I did any more coding to the base of this web program. So I ran pytest on my docker container and everything ran fine locally. So it was adjusting and fixing the build and push docker commands. Main issue was out of date versions of the dependencies in the requirements.txt which I updated and added my docker user and password to github's secret variable. After that, the actions worked. Now I wanted to see how the code ran on the user's end. That's when I encountered my first issue. I set up the mailtrap but the email verification link being sent wasn't verifying the account and locking the user out. I updated the create function in the UserService class to switch around the code since it was in the wrong order, and that worked perfectly! Next issue I faced was more of a preference issue to avoid confusion. Under login, it was asking for the user name, but it really wants an email. I felt users might be confused by this and so I overriden fastapi's "username" to say email instead. That was simple enough, but I was having issues where a new update for h11 was implemented in github actions but not an update for http. So I had to create a trivy ignore to ignore this particular issue since it could not be fixed on my own accord.

Then my feature came into play where I wanted to have users upload a profile picture to their account for personalization. I used MinIO to implement this where it would store all the photos uploaded in a bucket. I had to do some research of my own to really totally understand what MinIO did and why it was different than postgres. However, learning MinIO came from mistakes more than just reading. So I set up the localhost endpoint to 9000 and 9001 and used docker to download MinIO for my project. And I created a new function in user_services and user_routes to make a new function for FastAPI. However, I was missing a critical detail, I needed a minio_client code which I put under utilities. I also put save_image and get_image functions in there as well for simplicity sake. Then through a bit of trial and error, the first version of the profile picture code was complete with the ability for users to upload a photo. Next was having the users look at that photo and setting a default photo for new users. I did this by finding a default user image and put it in my settings folder. When the code began, it would upload that photo into the MinIO bucket (if it wasn't already there) and I rewrote the create function to set that image as the default. I also changed the url of profile pictures to just be the picture itself in the bucket instead of a link. With that, I now had to see if it worked with a get picture function. I already had get_image in my minIO and now incorporating a new function in the services and router to let users use the feature. Once that was done, I found out it was spitting out the text of the image and not the actual image. I tried to figure out a way to show the image, and I came up with using the IO library. That now was spitting out the image in the browser. That leaves my final issue, making sure the sizes of the profile pictures are consistent. I set the size to be 236x236 pixels since that is the size of the default user picture. I did this by changing the upload to have a file size limit of 2 MB and whenever a photo is uploaded, it will shrink to the size needed. This was done by overriding fastAPI's default settings in the upload function. 

My next part of this was getting tests for all the new features I added. I ran the coverage of pytest just to see what the current percentage was, which was around 89% when I needed to make sure it was above 90%. I started with adding three tests dedicated to my user services functions so I was testing the upload and get abilities. Then I jumped to adding a new python file for my minio_client test, which ended up being a massive challenge. I was originally using a mock MinIO bucket but then that would fail on github actions. I tried to rewrite the production.yml to have github actions implement a MinIO server. When that wasn't working, I decided to rewrite my tests for the minio_client which is when I found out I was mocking the MinIO wrong. I also added a few more tests for codes that were not covered as much. Since tests were working locally on Docker, I uploaded to github, and my user_services functions were failing there. So I eventually went back into it and fixed my problem and it worked on github after that!

Overall, this course was very informative and gave me a lot of opportunity to learn which I took full-heartedly. I enjoyed in person classes as well as doing the homeworks, even when I had problems with them. I want to thank Professor Williams for mental stimulating projects and insightful class lectures.

## 1 Feature

Uploading and Looking at Profile Pictures using MinIO [here](app/utils/minio_client.py)

## 5 QA Issues Solved

1. Email Verification Not Working [here](https://github.com/gvargaNJIT/user_management/issues/1)
2. Email Instead of Username [here](https://github.com/gvargaNJIT/user_management/issues/4)
3. Profile Picture Upload [here](https://github.com/gvargaNJIT/user_management/issues/3)
4. Get Profile Picture and Default [here](https://github.com/gvargaNJIT/user_management/issues/11)
5. Maximum size of picture file and resize [here](https://github.com/gvargaNJIT/user_management/issues/13)

## 10+ New Tests

3 New Tests for user_service [here](tests/test_services/test_user_service.py)
9 New Tests for minio_client [here](tests/test_minio_client.py)

Dockerhub Image for this project [here](https://hub.docker.com/layers/nickanick99/user_management/0400f28a6b97d7b1ac2bbf1d686d90ad83b4f275/images/sha256-3564c1ba3089d23ff88a82a3bc02b9934393ede76cdf54cfebab2e79a71c4a1b?tab=layers)

Everything below this line is the project guidelines from my professor
____________________________________________________________________________________________

# The User Management System Final Project: Your Epic Coding Adventure Awaits! 🎉✨🔥

## Introduction: Buckle Up for the Ride of a Lifetime 🚀🎬

Welcome to the User Management System project - an epic open-source adventure crafted by the legendary Professor Keith Williams for his rockstar students at NJIT! 🏫👨‍🏫⭐ This project is your gateway to coding glory, providing a bulletproof foundation for a user management system that will blow your mind! 🤯 You'll bridge the gap between the realms of seasoned software pros and aspiring student developers like yourselves. 

### [Instructor Video - Project Overview and Tips](https://youtu.be/gairLNAp6mA) 🎥

- [Introduction to the system features and overview of the project - please read](system_documentation.md) 📚
- [Project Setup Instructions](setup.md) ⚒️
- [Features to Select From](features.md) 🛠️
- [About the Project](about.md)🔥🌟

## Goals and Objectives: Unlock Your Coding Superpowers 🎯🏆🌟

Get ready to ascend to new heights with this legendary project:

1. **Practical Experience**: Dive headfirst into a real-world codebase, collaborate with your teammates, and contribute to an open-source project like a seasoned pro! 💻👩‍💻🔥
2. **Quality Assurance**: Develop ninja-level skills in identifying and resolving bugs, ensuring your code quality and reliability are out of this world. 🐞🔍⚡
3. **Test Coverage**: Write additional tests to cover edge cases, error scenarios, and important functionalities - leave no stone unturned and no bug left behind! ✅🧪🕵️‍♂️
4. **Feature Implementation**: Implement a brand new, mind-blowing feature and make your epic mark on the project, following best practices for coding, testing, and documentation like a true artisan. ✨🚀🎆
5. **Collaboration**: Foster teamwork and collaboration through code reviews, issue tracking, and adhering to contribution guidelines - teamwork makes the dream work, and together you'll conquer worlds! 🤝💪🌍
6. **Industry Readiness**: Prepare for the software industry by working on a project that simulates real-world development scenarios - level up your skills to super hero status  and become an unstoppable coding force! 🔝🚀🏆⚡

## Submission and Grading: Your Chance to Shine 📝✏️📈

1. **Reflection Document**: Submit a 1-2 page Word document reflecting on your learnings throughout the course and your experience working on this epic project. Include links to the closed issues for the **5 QA issues, 10 NEW tests, and 1 Feature** you'll be graded on. Make sure your project successfully deploys to DockerHub and include a link to your Docker repository in the document - let your work speak for itself! 📄🔗💥

2. **Commit History**: Show off your consistent hard work through your commit history like a true coding warrior. **Projects with less than 10 commits will get an automatic 0 - ouch!** 😬⚠️ A significant part of your project's evaluation will be based on your use of issues, commits, and following a professional development process like a boss - prove your coding prowess! 💻🔄🔥

3. **Deployability**: Broken projects that don't deploy to Dockerhub or pass all the automated tests on GitHub actions will face point deductions - nobody likes a buggy app! 🐞☠️ Show the world your flawless coding skills!

## Managing the Project Workload: Stay Focused, Stay Victorious ⏱️🧠⚡

This project requires effective time management and a well-planned strategy, but fear not - you've got this! Follow these steps to ensure a successful (and sane!) project outcome:

1. **Select a Feature**: [Choose a feature](features.md) from the provided list of additional improvements that sparks your interest and aligns with your goals like a laser beam. ✨⭐🎯 This is your chance to shine!

2. **Quality Assurance (QA)**: Thoroughly test the system's major functionalities related to your chosen feature and identify at least 5 issues or bugs like a true detective. Create GitHub issues for each identified problem, providing detailed descriptions and steps to reproduce - the more detail, the merrier! 🔍🐞🕵️‍♀️ Leave no stone unturned!

3. **Test Coverage Improvement**: Review the existing test suite and identify gaps in test coverage like a pro. Create 10 additional tests to cover edge cases, error scenarios, and important functionalities related to your chosen feature. Focus on areas such as user registration, login, authorization, and database interactions. Simulate the setup of the system as the admin user, then creating users, and updating user accounts - leave no stone unturned, no bug left behind! ✅🧪🔍🔬 Become the master of testing!

4. **New Feature Implementation**: Implement your chosen feature, following the project's coding practices and architecture like a coding ninja. Write appropriate tests to ensure your new feature is functional and reliable like a rock. Document the new feature, including its usage, configuration, and any necessary migrations - future you will thank you profusely! 🚀✨📝👩‍💻⚡ Make your mark on this project!

5. **Maintain a Working Main Branch**: Throughout the project, ensure you always have a working main branch deploying to Docker like a well-oiled machine. This will prevent any last-minute headaches and ensure a smooth submission process - no tears allowed, only triumphs! 😊🚢⚓ Stay focused, stay victorious!

Remember, it's more important to make something work reliably and be reasonably complete than to implement an overly complex feature. Focus on creating a feature that you can build upon or demonstrate in an interview setting - show off your skills like a rockstar! 💪🚀🎓

Don't forget to always have a working main branch deploying to Docker at all times. If you always have a working main branch, you will never be in jeopardy of receiving a very disappointing grade :-). Keep that main branch shining bright!

Let's embark on this epic coding adventure together and conquer the world of software engineering! You've got this, coding rockstars! 🚀🌟✨
