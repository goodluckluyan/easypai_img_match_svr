#include <getopt.h>
#include <dirent.h>
#include <unistd.h>
#include <sys/stat.h>
#include <vector>
#include <map>
#include <json/json.h>
#include "imagecompare.h"

using namespace std;


/* Show all files under dir_name , do not show directories ! */
int  showAllFiles( const char * dir_name ,vector<string> &vecfile,const char *filter)
{
    // check the parameter !
    if( NULL == dir_name )
    {
//        cout<<" dir_name is null ! "<<endl;
        return 1;
    }

    // check if dir_name is a valid dir
    struct stat s;
    lstat( dir_name , &s );
    if( ! S_ISDIR( s.st_mode ) )
    {
//        cout<<"dir_name is not a valid directory !"<<endl;
        return 2;
    }

    struct dirent * filename;    // return value for readdir()
    DIR * dir;                   // return value for opendir()
    dir = opendir( dir_name );
    if( NULL == dir )
    {
//        cout<<"Can not open dir "<<dir_name<<endl;
        return 2;
    }


    /* read all the files in the dir ~ */
    while( ( filename = readdir(dir) ) != NULL )
    {
        // get rid of "." and ".."
        if( strcmp( filename->d_name , "." ) == 0 ||
                strcmp( filename->d_name , "..") == 0 )
            continue;
        string name = filename->d_name;
        if(name.find(filter)!=string::npos)
        {
            string full_path = string(dir_name);
            if(full_path.rfind('/')!=full_path.size()-1)
            {
               full_path+="/";
            }
            full_path+=name;
            vecfile.push_back(full_path);
        }

    }
    return 0;
}



int main(int argc, char* argv[])
{

    char oc;
    std::string template_dir;
    std::string image_dir;
    int width = 0;
    int height = 0;
    std::string lubo_image_type = "jpg";
    float threshold = 0.008;
    if(argc <= 4)
    {
        printf("please input parameter:\n");
        printf("-i:lubo image dir -t:template image dir -w:template width -h:template height \n");
        printf("-y:lubo image type -h:match num threshold\n");
        return 1;
    }

    while((oc=getopt(argc,argv,"i:t:w:h:y:s"))!=-1)
    {
        switch(oc)
        {
        case 'i':
            image_dir = optarg;
            break;
        case 't':
            template_dir = optarg;
            break;
        case 'w':
            width = atoi(optarg);
            break;
        case 'h':
            height = atoi(optarg);
            break;
        case 'y':
            lubo_image_type = optarg;
            break;
        case 's':
            threshold = atof(optarg);
            break;
        }
    }

    vector<string> vecTemplateBmp;
    showAllFiles(template_dir.c_str(),vecTemplateBmp,".bmp");

    vector<string> vecTemplateSift;
    showAllFiles(template_dir.c_str(),vecTemplateSift,".sift");


    vector<string> vecLuboBmp;
    showAllFiles(image_dir.c_str(),vecLuboBmp,lubo_image_type.c_str());

    // 创建模板匹配实例
    TemplateCompare tc = TemplateCompare(vecTemplateBmp,vecLuboBmp,0,width,height,0.008);

    // 生成模板图片特征
    tc.GenerateTemplateFeature(vecTemplateSift);

    // 生成录播图片特征
    tc.GenerateLuboFeature();

    // 进行特征匹配
    map<string,vector<struct MatchInfo> > match_result;
    map<string,vector<struct MatchInfo> > ocr_result;
    tc.Compare(match_result,ocr_result);

    // 对匹配结果进行格式化输出，输出成Json字符串
    Json::Value result_json;
    map<string,vector<struct MatchInfo> >::iterator it = match_result.begin();
    for(;it != match_result.end(); it++)
    {
        Json::Value lubo;
        lubo["lubo_image"] = it->first;
        lubo["oper_type"] = "match";
        Json::Value matchresult;

        vector<struct MatchInfo> & vecMatchinfo = it->second;
        for(int i = 0;i <vecMatchinfo.size();i++)
        {
            Json::Value matchitem;
            struct MatchInfo &mi = vecMatchinfo[i];
            if(mi.weight > threshold)
            {
                matchitem["t_full_path"] = mi.template_image_path;
                matchitem["weight"] = mi.weight;
                matchitem["match_num"] = mi.match_num;
                matchitem["lubo_f_num"] = mi.lubo_feature_num;
                matchitem["t_f_num"] = mi.template_feature_num;
                matchresult.append(matchitem);
            }
        }
        lubo["match_result"] = matchresult;

        result_json.append(lubo);

    }

    map<string,vector<struct MatchInfo> >::iterator ocrit = ocr_result.begin();
    for(;ocrit != ocr_result.end(); ocrit++)
    {
        Json::Value ocrlubo;
        ocrlubo["lubo_image"] = ocrit->first;
        ocrlubo["oper_type"] = "ocr";
        Json::Value ocrresult;

        vector<struct MatchInfo> & vecOCRinfo = ocrit->second;
        for(int i = 0;i <vecOCRinfo.size();i++)
        {
            Json::Value ocritem;
            struct MatchInfo &mi = vecOCRinfo[i];
            ocritem["ocr"] = mi.ocr;
            ocrresult.append(ocritem);
        }

        ocrlubo["ocr_result"] = ocrresult;
        result_json.append(ocrlubo);
    }

    Json::Value find_result;
    if(ocr_result.size()==0 && match_result.size()==0)
    {
        find_result["result"].resize(0);
    }
    else
    {
        find_result["result"] = result_json;
    }
    Json::FastWriter writer;
    string result_json_str = writer.write(find_result);

    printf("%s",result_json_str.c_str());

    return 0;

}


