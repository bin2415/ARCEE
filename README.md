## ARCEE

### build

#### libmupdf

```
git clone --recursive git://git.ghostscript.com/mupdf.git
make HAVE_X11=no HAVE_GLUT=no prefix=/usr/local install -j
```

#### python dependency

```
pip install -r requirements.txt
```

#### Build AFL

```
pushd $PWD
cd AFL && make 
cd llvm_mode && make
popd
```

#### Install Convertors

```
sudo apt update 
sudo apt install wget xfonts-75dpi
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb
wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.bionic_amd64.deb
sudo apt install ./wkhtmltox_0.12.5-1.bionic_amd64.deb
```

#### build the tool

```
pushd $PWD
cd exchange_obj && make
popd
pushd $PWD
cd remove_font && make
popd
```


### Run


```
$ bash run_arcee.sh -h

$ This script is used to run the toolchains automatically!
	 -o <string>: output directory
	 -b <number>: batch number. How many htmls should generate at once. The default number is 2000
	 -e <number>: the number of pdfs that generated by exchanging objects componment. The default number is 4
	 -C <path of afl-cmin>: path of afl-cmin. default is afl-cmin
	 -M <path of afl-showmap>: path of afl-showmap. default is afl-showmap
	 -P <path of fuzzed pdf parser>
	 -T <timeout of afl-cmin>
	 -S <arguments of fuzzed pdf parser>
```

For example, if we want to run mutool

```
bash run_arcee.sh -o <output of seeds> -C <path of afl-cmin> -M <path of afl-showmap> -P <path of fuzzed mutool> -T 60 -S "draw @@"
```
