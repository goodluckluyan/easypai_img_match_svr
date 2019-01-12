import os
import json
import mylog

def gen_vf_info(filepath):
    cmd = '/usr/local/bin/ffprobe -v quiet -print_format json -show_format -show_streams -i %s'%filepath
    with os.popen(cmd) as pf:
       pret = pf.read()
    return pret

def get_vf_info(filepath, stream_info):
    vinfo = gen_vf_info(filepath)
    try:
        v_json = json.loads(vinfo)
        for stream in v_json['streams']:
            if stream['codec_type'] == 'video':
                stream_info['width'] = stream['width']
                stream_info['height'] = stream['height']
                stream_info['frame_rate'] = stream['avg_frame_rate']
        stream_info['duration'] = int(round(float(v_json['format']['duration'])))
    except Exception as e:
        print(Exception, e)
	

def fetch_image(video_path, frequency, image_w, image_h):
    dirname = os.path.dirname(video_path)
    cmd = '/usr/local/bin/ffmpeg -i %s -y -r %d -s %d*%d -f image2 %s/%s 2>/dev/null' % (video_path, frequency,
                                                                          image_w, image_h ,dirname, '%d.bmp')
    mylog.logger.info("%s" % cmd)
    os.system(cmd)


if __name__ == '__main__':
    video_path = '/root/easypai/bin/template/cs19010007/letv.mp4'
    stream={}
    get_vf_info(video_path,stream)
    print(stream)
    fetch_image(video_path,1,704,576)