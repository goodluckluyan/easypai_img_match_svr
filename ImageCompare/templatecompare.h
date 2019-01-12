#ifndef TEMPLATECOMPARE_H
#define TEMPLATECOMPARE_H
#include <string>
#include <vector>
#include <map>
#include <stdio.h>
#include "VideoCompareModule.h"
#include "opencv2/core.hpp"
#include "opencv2/imgproc/imgproc_c.h"
#include "opencv2/highgui.hpp"

using namespace std;
class PICTUR_ITEM
{
public:
    PICTUR_ITEM()
    {
        addr = NULL;
        length = 0;
        picture_order = 0;
        quantity = 0;
        width = 0;
        height = 0;
        operator_type = 0;
    }

    PICTUR_ITEM(const PICTUR_ITEM& obj)
    {
        if(obj.addr!=NULL&&obj.length>0)
        {
            addr = new char[obj.length];
            length = obj.length;
            memcpy(addr,obj.addr,length);
        }
        else
        {
            addr = obj.addr;
            length = obj.length;
        }
        picture_order = obj.picture_order;
        quantity = obj.quantity;
        featureFullFilename = obj.featureFullFilename;
        pictureFilename = obj.pictureFilename;
        pictureFullFilePath = obj.pictureFullFilePath;
        width = obj.width;
        height = obj.height;
    }

    PICTUR_ITEM& operator=(const PICTUR_ITEM& obj)
    {
        if(this != &obj)
        {
            if(obj.addr!=NULL&&obj.length>0)
            {
                addr = new char[obj.length];
                length = obj.length;
                memcpy(addr,obj.addr,length);
            }
            else
            {
                addr = obj.addr;
                length = obj.length;
            }

            picture_order = obj.picture_order;
            quantity = obj.quantity;
            featureFullFilename = obj.featureFullFilename;
            pictureFilename = obj.pictureFilename;
            pictureFullFilePath = obj.pictureFullFilePath;
            width = obj.width;
            height = obj.height;
        }
        return *this;
    }

    ~PICTUR_ITEM()
    {
        if(addr != NULL)
        {
            delete[] addr;
            addr = NULL;
            length = 0;
        }
    }

public:
    int picture_order;              ////bmp图片的序号
    unsigned int length;            ////地址长度
    char *addr;                     ///特征首地址
    int quantity;                   ///quantity  一张图片特征点数量
    int operator_type;              ///0:图片匹配 1:ocr
    unsigned int width;
    unsigned  int height;
    std::string featureFullFilename;
    std::string pictureFilename;          ///p图片文件名
    std::string pictureFullFilePath;      ///全图片路径，例如/home/zyh/mp4File/feature001/0.bmp

};
typedef vector<struct PICTUR_ITEM>PICTURE_VECTOR;

struct MatchInfo
{
  MatchInfo()
  {
      match_num = 0;
      lubo_feature_num = 0;
      template_feature_num = 0;
      weight = 0.0;
      operator_type = 0;
  }

  MatchInfo(const MatchInfo &obj)
  {
      template_image_path = obj.template_image_path;
      template_feature_num = obj.template_feature_num;
      lubo_feature_num = obj.lubo_feature_num;
      match_num = obj.match_num;
      weight = obj.weight;
      ocr = obj.ocr;
      operator_type = obj.operator_type;
  }

  MatchInfo& operator=(const MatchInfo& obj)
  {
      if(this!=&obj)
      {
          template_image_path = obj.template_image_path;
          template_feature_num = obj.template_feature_num;
          lubo_feature_num = obj.lubo_feature_num;
          match_num = obj.match_num;
          weight = obj.weight;
          ocr = obj.ocr;
          operator_type = obj.operator_type;
      }
      return *this;
  }

  string template_image_path;
  float weight;
  int match_num;
  int lubo_feature_num;
  int template_feature_num;
  string ocr;
  int operator_type ;
};

struct CompareMatchInfo
{
    bool operator()(const MatchInfo& first, const MatchInfo& second)
    {
         return first.match_num > second.match_num;
    }
};

class TemplateCompare
{
public:
    TemplateCompare(std::vector<string> &vecTemplatePath,std::vector<string> &vecLuboPath,
                    int ftype,int fweidht,int fheight,float threshold);
    ~TemplateCompare();
public:
    // 提取特征文件中的特征描述
    int GenerateTemplateFeature(vector<string> &vecFeatureFilename);

    // 提取录播图片中的特征
    int GenerateLuboFeature();

    // 清空模板特征
    int ClearTempalteFeature();

    // 情况录播特征
    int ClearLuboFeature();

    // 图片特征比对，以模板图为目标
    int Compare(map<string,vector<struct MatchInfo> > &match_result,
                map<string,vector<struct MatchInfo> > &ocr_result);

    // 在模板中搜索和录播图匹配的图像特征
    int SearchTemplate(PICTUR_ITEM& item,vector<struct MatchInfo> &vecMatch);
private:
    PICTURE_VECTOR m_vecTemplatePic;
    PICTURE_VECTOR m_vecLuboPic;
    int m_Feature_type;
    VideoCompareModule m_feature;
    int m_fWidth;
    int m_fHeigth;
    float m_threshold;

};

class ImgBuf
{
public:

    typedef struct BITMAPFILEHEADER
    {
        unsigned short bfType;
        unsigned int  bfSize;
        unsigned short bfReserved1;
        unsigned short bfReserved2;
        unsigned int bfOffBits;
    }__attribute__((packed)) BITMAPFILEHEADER;

    typedef struct BITMAPINFOHEADER
    {
        u_int32_t biSize;
        u_int32_t biWidth;
        u_int32_t biHeight;
        u_int16_t biPlanes;
        u_int16_t biBitCount;
        u_int32_t biCompression;
        u_int32_t biSizeImage;
        u_int32_t biXPelsPerMeter;
        u_int32_t biYPelsPerMeter;
        u_int32_t biClrUsed;
        u_int32_t biClrImportant;
    }__attribute__((packet)) BITMAPINFODEADER;

    ImgBuf(unsigned char * pRGB,long size,int width,int height)
    {
        m_pBGR24 =(char *) malloc(size);
//        cv::Mat dst(height,width,CV_8UC3,m_pBGR24);
//        cv::Mat src(height + height/2,width,CV_8UC1,pYUV);
//        cvtColor(src,dst,::CV_YUV2BGR_I420);//::CV_YUV2BGR_YV12
//        m_pInspectImg = new IplImage(dst);
        memcpy(m_pBGR24,pRGB,size);
        m_lsize = size;
        m_nWidth = width;
        m_nHeight = height;
        m_pRGB24_HR = NULL;
        m_pInspectImg = NULL;
    }

    ImgBuf(std::string &pImagePath)
    {
         m_ImagePath = pImagePath;
         m_pBGR24 = NULL;
         m_pRGB24_HR = NULL;
         m_pInspectImg = NULL;
    }

    ~ImgBuf()
    {

        if(m_pInspectImg !=NULL)
        {
            delete m_pInspectImg;
            m_pInspectImg = NULL;
        }

        if(m_pBGR24 != NULL)
        {
           free(m_pBGR24);
           m_pBGR24 = NULL;
        }

        if(m_pRGB24_HR != NULL)
        {
            free(m_pRGB24_HR);
            m_pRGB24_HR = NULL;
        }
    }

   // 读取
    int GetImage(unsigned char *pImageBuf,unsigned int &len)
    {
        if(m_pBGR24 == NULL)
        {
            CvMat* pimgmat = cvLoadImageM(m_ImagePath.c_str());
            CvMat* newimgmat = pimgmat;
            if(pimgmat->cols>4000 || pimgmat->rows > 4000)
            {
                int newwidth = pimgmat->cols/4;
                int newhight = pimgmat->rows/4;
                newimgmat = cvCreateMat(newwidth,newwidth,CV_8UC3);
                cvResize(newimgmat,pimgmat,CV_INTER_LINEAR);
            }
            else if(pimgmat->cols>2000 || pimgmat->rows > 2000)
            {
                int newwidth = pimgmat->cols/2;
                int newhight = pimgmat->rows/2;
                newimgmat = cvCreateMat(newhight,newwidth,CV_8UC3);
            }


            m_nWidth = newimgmat->cols;
            m_nHeight = newimgmat->rows;
            m_pBGR24 =(char *) malloc(m_nWidth*m_nHeight*3);
            CvMat dst;
            cvInitMatHeader(&dst,m_nHeight,m_nWidth,CV_8UC3,m_pBGR24);
            cvCopy(newimgmat,&dst);
            m_lsize = m_nWidth * m_nHeight *3;
            if(newimgmat != pimgmat)
            {
                cvReleaseMat(&newimgmat);
            }
        }

        if(m_pBGR24 != NULL&&m_lsize != 0 && pImageBuf != NULL && len >= m_lsize)
        {
             memcpy(pImageBuf,m_pBGR24,m_lsize);
             return m_lsize;
        }
        else if(pImageBuf == NULL && m_pBGR24 != NULL&&m_lsize != 0)
        {
            len = m_lsize;
            return 0;
        }

        return 0;
    }

    void SaveJpeg(std::string fullpath)
    {
        ::cvSaveImage(fullpath.c_str(),m_pInspectImg);
    }

    void Savebmp(std::string fullpath)
    {

        int lineBytes = m_nWidth*3;
        FILE *pDestFile = fopen(fullpath.c_str(), "wb");
        if(NULL == pDestFile)
        {
            printf("open file %s failed\n",fullpath.c_str());
            return;
        }
        BITMAPFILEHEADER btfileHeader;
        btfileHeader.bfType = 0x4d42;//mb
        btfileHeader.bfSize = lineBytes*m_nHeight;
        btfileHeader.bfReserved1 = 0;
        btfileHeader.bfReserved2 = 0;
        btfileHeader.bfOffBits = sizeof(BITMAPFILEHEADER);

        BITMAPINFOHEADER bitmapinfoheader;
        bitmapinfoheader.biSize = 40;
        bitmapinfoheader.biWidth = m_nWidth;
        bitmapinfoheader.biHeight = m_nHeight;
        bitmapinfoheader.biPlanes = 1;
        bitmapinfoheader.biBitCount = 24;
        bitmapinfoheader.biCompression = 0;
        bitmapinfoheader.biSizeImage = lineBytes*m_nHeight;
        bitmapinfoheader.biXPelsPerMeter = 0;
        bitmapinfoheader.biYPelsPerMeter = 0;
        bitmapinfoheader.biClrUsed = 0;
        bitmapinfoheader.biClrImportant = 0;

        int i=0;
        fwrite(&btfileHeader, sizeof(BITMAPFILEHEADER), 1, pDestFile);
        fwrite(&bitmapinfoheader, sizeof(BITMAPINFODEADER), 1, pDestFile);
        for(i=m_nHeight-1; i>=0; i--)
        {
           fwrite(m_pBGR24+i*lineBytes, lineBytes, 1, pDestFile);
        }

        fclose(pDestFile);
    }

    void Savebmp_HR(std::string fullpath,int width,int height)
    {

        FILE *pDestFile = fopen(fullpath.c_str(), "wb");
        if(NULL == pDestFile)
        {
            printf("open file %s failed\n",fullpath.c_str());
            return;
        }

        BITMAPFILEHEADER btfileHeader;
        btfileHeader.bfType = 0x4d42;//mb
        btfileHeader.bfSize = m_linesize_hr*height;
        btfileHeader.bfReserved1 = 0;
        btfileHeader.bfReserved2 = 0;
        btfileHeader.bfOffBits = sizeof(BITMAPFILEHEADER);

        BITMAPINFOHEADER bitmapinfoheader;
        bitmapinfoheader.biSize = 40;
        bitmapinfoheader.biWidth = width;
        bitmapinfoheader.biHeight = height;
        bitmapinfoheader.biPlanes = 1;
        bitmapinfoheader.biBitCount = 24;
        bitmapinfoheader.biCompression = 0;
        bitmapinfoheader.biSizeImage = m_linesize_hr*height;
        bitmapinfoheader.biXPelsPerMeter = 0;
        bitmapinfoheader.biYPelsPerMeter = 0;
        bitmapinfoheader.biClrUsed = 0;
        bitmapinfoheader.biClrImportant = 0;

        int i=0;
        fwrite(&btfileHeader, sizeof(BITMAPFILEHEADER), 1, pDestFile);
        fwrite(&bitmapinfoheader, sizeof(BITMAPINFODEADER), 1, pDestFile);
        for(i=height-1; i>=0; i--)
        {
           fwrite(m_pRGB24_HR+i*m_linesize_hr, m_linesize_hr, 1, pDestFile);
        }

        fclose(pDestFile);
    }

    char * SetHRRect(int left,int top,int right,int bottom)
    {
        int width = right - left;
        int height = bottom - top;
        m_linesize_hr = ((width*24+31)>>5)<<2; //补零后的每行的长度
        m_lsize_hr = m_linesize_hr*height;
        m_pRGB24_HR = (char *) malloc(m_lsize_hr);
        memset(m_pRGB24_HR,0,m_lsize_hr);
        int linesize = width*3;
        int rawlinesize = m_nWidth*3;
        int rawstart = (top-1)*rawlinesize+left*3;

        for(int i = 0 ;i < height ;i++)
        {
            memcpy(m_pRGB24_HR+m_linesize_hr*i,m_pBGR24+rawstart+rawlinesize*i,linesize);
        }
        return m_pRGB24_HR;

    }
public:

    char * m_pBGR24;
    char * m_pRGB24_HR;// 热点区域
    IplImage *m_pInspectImg;
    std::string m_ImagePath;

    unsigned int m_lsize;
    unsigned int m_lsize_hr;
    unsigned int m_linesize_hr;
    unsigned int m_nWidth;
    unsigned int m_nHeight;
    unsigned int m_nCompareCnt;
};
#endif // TEMPLATECOMPARE_H
