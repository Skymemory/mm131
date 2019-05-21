# mm131
Batch picture downloader for mm131

#### 依赖

Python >= 3.7


#### 实现原理

mm131网站上的一张图片由一个二元组标识（一级索引，二级索引），其中二级索引的范围是可以获取到的

比如某个分类下妹子的图片地址为:[http://www.mm131.com/xinggan/4100.html](http://www.mm131.com/xinggan/4100.html)，其中4100就是一级索引编号，在该页面解析html获取到总共页数也就间接知道了二级索引的范围，这样就能批量的下载图片啦

#### 使用方式

mm131.py提供了几个选项说明，通过`python test.py -h`可参看:

```shell
usage: mm131.py [-h] [-c CATEGORY] [-r RANGE] [-d DIRECTORY] [--level LEVEL]

Picture downloader for mm131

optional arguments:
  -h, --help     show this help message and exit
  -c CATEGORY    Specify which category to download(default xinggan)
  -r RANGE       Specify first index,format: start[,end]
  -d DIRECTORY   Save directory(default /tmp)
  --level LEVEL  Logging level
```



- `-c`：指定下载图片的分类，默认xinggan
- `-r`：指定一级索引范围
- `-d`：指定保存目录，默认/tmp目录
- `—level`：日志打印级别

比如下载一级索引为4100图片:

```shell
> python mm131.py -r 4100
INFO:root:-----------------statistics------------------
INFO:root:Success:65		Fail:0
INFO:root:Cost time:1.678253173828125
```

