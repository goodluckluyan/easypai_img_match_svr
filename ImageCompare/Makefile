HEADFLAG = -I/home/ubuntu/opencv-2.4.13/inclue -I/usr/include/jsoncpp
LDFLAG = -Wl,-rpath=/home/ubuntu/opencv-2.4.13/lib -L/home/ubuntu/opencv-2.4.13/lib -lopencv_core -lopencv_highgui -lopencv_imgproc -lgdk-x11-2.0 -ljsoncpp

imagecompare:templatecompare.o imagecompare.o
	g++ -std=c++11 -o $@  $^ ./libvideocompare.a $(LDFLAG)
templatecompare.o:templatecompare.cpp templatecompare.h
	g++ -g -c $(HEADFLAG) -std=c++11  ./templatecompare.cpp 
imagecompare.o:imagecompare.cpp imagecompare.h
	g++ -g -c $(HEADFLAG) -std=c++11  ./imagecompare.cpp

