#include "VideoCompareModule.h"
#include <getopt.h>
#include <string>
#include <stdio.h>
void printhelp()
{
   printf("please input parameter:\n");
   printf("-t :feature type surf or sift -i : bmp file path -o :output feature file path\n");
}


int main(int argc,char*argv[])
{
    int nType=0;
    std::string type="sift";
    std::string input_file;
    std::string output_file;
    char oc;
    while((oc=getopt(argc,argv,"t:i:o:"))!=-1)
    {
       switch(oc)
       {
          case 't':
	    type=std::string(optarg);
	    break;
	  case 'i':
	    input_file=std::string(optarg);
	    break;
	  case 'o':
	    output_file=std::string(optarg);
	    break;
       }
    }
    if(input_file.empty()||(type != "sift"&&type != "surf"))
    {
       printhelp();  
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
      
       printf("input file name error,must be file type is bmp!(%s)\n",input_file.c_str());
       return -1;
    }
    std::string all_filename = input_file.substr(0,pos);
    if(output_file.empty())
    {
      output_file = all_filename+"."+type;  
    }
    
    int featurenum = 0;
    VideoCompareModule vcm;
    if(type=="surf")
    {
      nType = 1;
    }
    else
    {
      nType = 0;  
    }
    vcm.InitModule(nType);
    int ret = vcm.ExportFeature(input_file.c_str(),output_file.c_str(),featurenum);

    // 把特征数量加入文件名
    std::string add_featurenum_filename = output_file;
    char featurenum_buf[32]={'\0'};
    snprintf(featurenum_buf,sizeof(featurenum_buf),"_%d.%s",featurenum,type.c_str());
    std::string expand_name = std::string(".")+type;
    size_t epos = add_featurenum_filename.find(expand_name.c_str());
    if(epos != std::string::npos)
    {
         add_featurenum_filename.replace(epos,expand_name.size(),featurenum_buf);
         if(rename(output_file.c_str(),add_featurenum_filename.c_str())!=0)
         {
            ret = 1;
         }
    }
    printf("%d\n",featurenum);
    return ret;
}
