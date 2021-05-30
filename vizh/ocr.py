import ctypes
import locale
import os
import os.path
import platform
from ctypes.util import find_library

import cffi
import numpy as np

ffi = cffi.FFI()
ffi.cdef("""
    typedef signed char             l_int8;
    typedef unsigned char           l_uint8;
    typedef short                   l_int16;
    typedef unsigned short          l_uint16;
    typedef int                     l_int32;
    typedef unsigned int            l_uint32;
    typedef float                   l_float32;
    typedef double                  l_float64;
    typedef long long               l_int64;
    typedef unsigned long long      l_uint64;
    typedef int l_ok; /*!< return type 0 if OK, 1 on error */
    
    
    struct Pix;
    typedef struct Pix PIX;
    typedef enum lept_img_format {
        IFF_UNKNOWN        = 0,
        IFF_BMP            = 1,
        IFF_JFIF_JPEG      = 2,
        IFF_PNG            = 3,
        IFF_TIFF           = 4,
        IFF_TIFF_PACKBITS  = 5,
        IFF_TIFF_RLE       = 6,
        IFF_TIFF_G3        = 7,
        IFF_TIFF_G4        = 8,
        IFF_TIFF_LZW       = 9,
        IFF_TIFF_ZIP       = 10,
        IFF_PNM            = 11,
        IFF_PS             = 12,
        IFF_GIF            = 13,
        IFF_JP2            = 14,
        IFF_WEBP           = 15,
        IFF_LPDF           = 16,
        IFF_TIFF_JPEG      = 17,
        IFF_DEFAULT        = 18,
        IFF_SPIX           = 19
    };
    
    char * getLeptonicaVersion (  );
    PIX * pixRead ( const char *filename );
    PIX * pixCreate ( int width, int height, int depth );
    PIX * pixEndianByteSwapNew(PIX  *pixs);
    l_int32 pixSetData ( PIX *pix, l_uint32 *data );
    l_ok pixSetPixel ( PIX *pix, l_int32 x, l_int32 y, l_uint32 val );
    l_ok pixSetRGBPixel ( PIX *pix, l_int32 x, l_int32 y, l_uint32 r, l_uint32 g, l_uint32 b );
    l_ok pixWrite ( const char *fname, PIX *pix, l_int32 format );
    l_int32 pixFindSkew ( PIX *pixs, l_float32 *pangle, l_float32 *pconf );
    PIX * pixDeskew ( PIX *pixs, l_int32 redsearch );
    void pixDestroy ( PIX **ppix );
    l_ok pixGetResolution ( const PIX *pix, l_int32 *pxres, l_int32 *pyres );
    l_ok pixSetResolution ( PIX *pix, l_int32 xres, l_int32 yres );
    l_int32 pixGetWidth ( const PIX *pix );
    l_int32 pixDisplay( PIX *pixs, l_int32 x, l_int32 y );
    void setLeptDebugOK( l_int32 okay );
    
    typedef struct TessBaseAPI TessBaseAPI;
    typedef struct ETEXT_DESC ETEXT_DESC;
    typedef struct TessPageIterator TessPageIterator;
    typedef struct TessResultIterator TessResultIterator;
    typedef int BOOL;
    
    typedef enum TessPageSegMode {
        PSM_OSD_ONLY               =  0,
        PSM_AUTO_OSD               =  1,
        PSM_AUTO_ONLY              =  2,
        PSM_AUTO                   =  3,
        PSM_SINGLE_COLUMN          =  4,
        PSM_SINGLE_BLOCK_VERT_TEXT =  5,
        PSM_SINGLE_BLOCK           =  6,
        PSM_SINGLE_LINE            =  7,
        PSM_SINGLE_WORD            =  8,
        PSM_CIRCLE_WORD            =  9,
        PSM_SINGLE_CHAR            = 10,
        PSM_SPARSE_TEXT            = 11,
        PSM_SPARSE_TEXT_OSD        = 12,
        PSM_COUNT                  = 13} TessPageSegMode;

    TessBaseAPI* TessBaseAPICreate();
    int    TessBaseAPIInit3(TessBaseAPI* handle, const char* datapath, const char* language);
    void   TessBaseAPISetPageSegMode(TessBaseAPI* handle, TessPageSegMode mode);
    void   TessBaseAPISetImage(TessBaseAPI* handle,
                               const unsigned char* imagedata, int width, int height,
                               int bytes_per_pixel, int bytes_per_line);
    void   TessBaseAPISetImage2(TessBaseAPI* handle, struct Pix* pix);
    
    BOOL   TessBaseAPISetVariable(TessBaseAPI* handle, const char* name, const char* value);
    int TessBaseAPIRecognize(TessBaseAPI* handle, ETEXT_DESC* monitor);
    char*  TessBaseAPIGetUTF8Text(TessBaseAPI* handle);
    void   TessDeleteText(char* text);
  
    void   TessBaseAPIEnd(TessBaseAPI* handle);
    void   TessBaseAPIDelete(TessBaseAPI* handle);
    """)


def matToPix8(leptonica, im):
    """Convert OpenCV image to leptonica PIX."""
    height, width = len(im), len(im[0])
    depth = 32 if type(im[0][0]) is np.ndarray else 8
    pixs = leptonica.pixCreate(width, height, depth)

    for (y, row) in enumerate(im):
        for (x, pixel) in enumerate(row):
            if type(pixel) is np.ndarray:
                leptonica.pixSetRGBPixel(pixs, x, y, pixel[0], pixel[1], pixel[2])
            else:
                leptonica.pixSetPixel(pixs, x, y, pixel)
                
    return pixs

class TesseractOCR(object):
    def __init__(self):
        pass
        self.zlib = ffi.dlopen(find_library('zlib1' if os.name == 'nt' else 'z'))
        self.leptonica = ffi.dlopen(find_library('liblept-5' if os.name == 'nt' else 'lept'))
        tess_lib = find_library('libtesseract-4' if os.name == 'nt' else 'tesseract')
        self.tesseract = ffi.dlopen(tess_lib)

        self.api = self.tesseract.TessBaseAPICreate()

        tess_data_dir = os.environ['TESSDATA_PREFIX'] if 'TESSDATA_PREFIX' in os.environ else None
        # On Windows tessdata is in the same directory as the library
        tess_data_dir = tess_data_dir or os.path.join(os.path.dirname(tess_lib), 'tessdata')
        tess_data_bytes = tess_data_dir.encode('utf-8')
        self.tesseract.TessBaseAPIInit3(self.api, tess_data_bytes, ffi.NULL)
        self.tesseract.TessBaseAPISetPageSegMode(self.api, self.tesseract.PSM_SINGLE_LINE)
        self.tesseract.TessBaseAPISetVariable(self.api, "user_defined_dpi".encode('utf-8'), "300".encode('utf-8'))
    
    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.tesseract.TessBaseAPIEnd(self.api)
        self.tesseract.TessBaseAPIDelete(self.api)
        ffi.dlclose(self.zlib)
        ffi.dlclose(self.leptonica)
        ffi.dlclose(self.tesseract)

    def ocr(self, image):
        pix = matToPix8(self.leptonica, image)
        self.tesseract.TessBaseAPISetImage2(self.api, pix)
        self.tesseract.TessBaseAPIRecognize(
            self.api, ffi.NULL)

        text = self.tesseract.TessBaseAPIGetUTF8Text(self.api)
        decoded_text = ffi.string(text).decode('utf-8')

        self.tesseract.TessDeleteText(text)
        pix_ptr = ffi.new('PIX*[1]')
        pix_ptr[0] = pix
        self.leptonica.pixDestroy(pix_ptr)

        return decoded_text

