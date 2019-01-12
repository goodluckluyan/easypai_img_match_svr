#include <unistd.h>
#include <algorithm>
#include "templatecompare.h"

using namespace std;

#define FEATURE_ITEM_LEN 1024
TemplateCompare::TemplateCompare(std::vector<string> &vecTemplatePath,
                                 std::vector<string> &vecLuboPath,int ftype,
                                 int width,int height,float threshold)
{
    for(int i = 0 ;i < vecTemplatePath.size();i++)
    {
        PICTUR_ITEM t_item;
        t_item.pictureFullFilePath = vecTemplatePath[i];
        m_vecTemplatePic.push_back(t_item);
    }

    for(int j = 0;j < vecLuboPath.size();j++)
    {
        PICTUR_ITEM t_item;
        t_item.pictureFullFilePath = vecLuboPath[j];
        m_vecLuboPic.push_back(t_item);
    }
    m_Feature_type = ftype;
    m_fWidth = width;
    m_fHeigth = height;
    m_threshold = threshold;

}

TemplateCompare::~TemplateCompare()
{
    ClearTempalteFeature();
    ClearLuboFeature();
}

int TemplateCompare::GenerateTemplateFeature(vector<string> &vecFeatureFilename)
{
    m_feature.InitModule(m_Feature_type);
    for(int i = 0 ;i < m_vecTemplatePic.size();i++)
    {
        PICTUR_ITEM& t_item = m_vecTemplatePic[i];
        int ret = access(t_item.pictureFullFilePath.c_str(),F_OK);
        if(ret != 0)
        {
            continue;
        }

        size_t pos = t_item.pictureFullFilePath.rfind('/');
        t_item.pictureFilename=t_item.pictureFullFilePath.substr(pos+1);
        string dirname = t_item.pictureFullFilePath.substr(0,pos+1);
        size_t dotpos = t_item.pictureFilename.find(".bmp");
        std::string f_filename = t_item.pictureFilename.substr(0,dotpos);
        t_item.picture_order = atoi(f_filename.c_str());
        t_item.height = m_fHeigth;
        t_item.width = m_fWidth;
        f_filename = f_filename + "_";
        // 查找特征文件名
        for(int j = 0 ;j < vecFeatureFilename.size();j++)
        {
            string& tmp = vecFeatureFilename[j];
            size_t pos = tmp.find(f_filename.c_str());
            if(pos != string::npos)
            {
                t_item.featureFullFilename = tmp;
                break;
            }
        }

        ret = access(t_item.featureFullFilename.c_str(),F_OK);
        if(ret != 0)
        {
            continue;
        }

        size_t begin = t_item.featureFullFilename.rfind('_');
        size_t end = t_item.featureFullFilename.rfind('.');
        string fnum = t_item.featureFullFilename.substr(begin+1,end-begin-1);

        int featurenum = 0;
        featurenum = atoi(fnum.c_str());
        if(featurenum > 0)
        {
            unsigned int bufflen;
            t_item.addr = new char[featurenum*FEATURE_ITEM_LEN];
            m_feature.ImportFeature(t_item.featureFullFilename.c_str(),featurenum,t_item.addr,bufflen);
            t_item.length = bufflen;
            t_item.quantity = featurenum;
        }


    }
    return 0;
}


int TemplateCompare::GenerateLuboFeature()
{
    for(int j = 0;j < m_vecLuboPic.size();j++)
    {
        PICTUR_ITEM& t_item = m_vecLuboPic[j];
        int ret = access(t_item.pictureFullFilePath.c_str(),F_OK);
        if(ret != 0)
        {
            continue;
        }


        size_t pos = t_item.pictureFullFilePath.rfind('/');
        t_item.pictureFilename=t_item.pictureFullFilePath.substr(pos+1);
        string dirname = t_item.pictureFullFilePath.substr(0,pos+1);
        size_t dotpos = t_item.pictureFilename.find('.');
        std::string f_filename = t_item.pictureFilename.substr(0,dotpos);
        ImgBuf img = ImgBuf(t_item.pictureFullFilePath);
        unsigned int imgbuflen=0;
        img.GetImage(NULL,imgbuflen);
        if(imgbuflen > 0)
        {
            char *imagebuf = new char[imgbuflen];
            img.GetImage((unsigned char *)imagebuf,imgbuflen);
            t_item.height = img.m_nHeight;
            t_item.width = img.m_nWidth;
            if(t_item.pictureFilename.find("ocr")!=std::string::npos)
            {
                t_item.operator_type = 1;// ocr
            }
            else
            {
                t_item.operator_type = 0;// image match
                int featurenum = 0;
                m_feature.ExportFeature((const char *)imagebuf,imgbuflen,t_item.width,t_item.height,featurenum);
                if(featurenum > 0)
                {
                    unsigned int fbuflen = featurenum*FEATURE_ITEM_LEN;
                    t_item.addr = new char[fbuflen];
                    m_feature.GetFeatureBuffer(t_item.addr,fbuflen);
                    t_item.length = fbuflen;
                    t_item.quantity = featurenum;
                }
                delete[] imagebuf;
            }
        }
    }
    return 0;
}

int TemplateCompare::ClearTempalteFeature()
{
    for(int i = 0 ;i < m_vecTemplatePic.size();i++)
    {
        PICTUR_ITEM& t_item = m_vecTemplatePic[i];
        if(t_item.addr != NULL)
        {
            delete[] t_item.addr;
            t_item.addr = NULL;
            t_item.length = 0;
        }

    }
    m_vecTemplatePic.clear();

    return 0;
}

int TemplateCompare::ClearLuboFeature()
{
    for(int j = 0;j < m_vecLuboPic.size();j++)
    {
        PICTUR_ITEM& t_item = m_vecLuboPic[j];
        if(t_item.addr != NULL)
        {
            delete[] t_item.addr;
            t_item.addr = NULL;
            t_item.length = 0;
        }
    }
    m_vecLuboPic.clear();
     return 0;
}

int  TemplateCompare::SearchTemplate(PICTUR_ITEM& lubo_item,vector<struct MatchInfo> &vecMatch)
{



    for(int i = 0 ;i < m_vecTemplatePic.size();i++)
    {
        PICTUR_ITEM& t_item = m_vecTemplatePic[i];
        int matchcnt = 0;
        unsigned int width = t_item.width;
        unsigned int height = t_item.height;
        unsigned int owidth = lubo_item.width;
        unsigned int oheight = lubo_item.height;
        if(t_item.quantity == 0 )
        {
            continue;
        }

        m_feature.CompareFeature((char *)t_item.addr,
                                t_item.length,
                                width,
                                height,
                                t_item.quantity,
                                (char *)lubo_item.addr,
                                lubo_item.length,
                                owidth,
                                oheight,
                                lubo_item.quantity,
                                matchcnt);
        float weight = static_cast<float>(matchcnt)/((t_item.quantity+lubo_item.quantity)/2);
//      if(weight >= m_threshold )
        if(matchcnt > 0)
        {
            // 记录匹配对
            MatchInfo mi;
            mi.template_image_path = t_item.pictureFullFilePath;
            mi.lubo_feature_num = lubo_item.quantity;
            mi.template_feature_num = t_item.quantity;
            mi.weight = weight;
            mi.match_num = matchcnt;
            vecMatch.push_back(mi);
        }

    }
}

int TemplateCompare::Compare(map<string,vector<struct MatchInfo> > &match_result,
                             map<string,vector<struct MatchInfo> > &ocr_result)
{
    // 以模板图为目标进行模板搜索，得到录播的匹配结果
    for(int i = 0;i < m_vecLuboPic.size();i++)
    {
       PICTUR_ITEM& i_item = m_vecLuboPic[i];

       if(i_item.operator_type == 0)// 图像匹配
       {
           if(i_item.quantity == 0)
           {
               continue;
           }
           vector<MatchInfo> vecMatch;
           SearchTemplate(i_item,vecMatch);
           if(vecMatch.size()>0)
           {
                std::sort(vecMatch.begin(),vecMatch.end(),CompareMatchInfo());
                match_result[i_item.pictureFullFilePath] = vecMatch;
           }
       }
       else // ocr 为了兼容图像匹配结果强行加入，以后会改
       {
           MatchInfo mi;
           mi.ocr="ocr function uncomplete";
           mi.operator_type = i_item.picture_order;
           vector<MatchInfo> vecMatch;
           vecMatch.push_back(mi);
           ocr_result[i_item.pictureFullFilePath] = vecMatch;
       }

    }

  return 0;
}
