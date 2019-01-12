// 本源码目的是生成so，由于libvideocompare.a没有使用-PIC编译所以无法生成so
//
#include "VideoCompareModule.h"
#include <getopt.h>
#include <string>
#include <stdio.h>

//
// 
int extrace_feature(std::string &input_file,std::string &output_file,std::string &feature_type )
{
    int nType=0;
    if(input_file.empty()||(feature_type != "sift"&&feature_type != "surf"))
    {
       printf("input file is empty or feature type invalidate\n");  
       return -1;
    }
    
    size_t pos = input_file.rfind('.');
    if(pos == std::string::npos)
    {
       printf("input file name error(%s)\n",input_file.c_str());
       return -1;
    }
    std::string ext_name = input_file.substr(pos+1);
    if(ext_name!="bmp")
    {
      
       printf("input file name error,must be file feature_type is bmp!(%s)\n",input_file.c_str());
       return -1;
    }
    std::string all_filename = input_file.substr(0,pos);
    if(output_file.empty())
    {
      output_file = all_filename+"."+feature_type;  
    }
    
    int featurenum = 0;
    VideoCompareModule vcm;
    if(feature_type=="surf")
    {
      nType = 1;
    }
    else
    {
      nType = 0;  
    }
    vcm.InitModule(nType);
    int ret = vcm.ExportFeature(input_file.c_str(),output_file.c_str(),featurenum);
    printf("Export Feature ret :%d,Feature num:%d\n",ret,featurenum);
    return ret;
}
