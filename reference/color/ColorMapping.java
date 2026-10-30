package edu.SJTU.zhusy54.colorTrans;

import android.graphics.Color;

public class ColorMapping {
	private int[] colorMap, colorMapRef;

	public ColorMapping(int colorNum) {
		colorMap = new int[colorNum];
		colorMapRef = new int[colorNum];
		float[] colorHSV = new float[3];
//		float[] color64={355.37f, 1.97f, 16.03f, 23.19f, 29.15f, 34.54f, 39.63f, 44.54f, 
//				49.68f, 54.77f, 60.17f, 66.8f, 71.96f, 76.12f, 80.24f, 83.99f, 
//				87.58f, 91.18f, 95.09f, 99.63f, 105.27f, 111.37f, 131.83f, 139.6f, 
//				144.54f, 148.89f, 153.08f, 157.03f, 160.68f, 164.21f, 168.4f, 173.52f, 
//				180f, 186.14f, 190.81f, 194.86f, 198.82f, 203.82f, 209.91f, 215.59f, 
//				221.55f, 229.11f, 249.84f, 262.71f, 267.98f, 271.76f, 275.52f, 279.26f, 
//				282.76f, 286.22f, 289.7f, 293.23f, 297.01f, 301.72f, 306.3f, 310.85f, 
//				315.53f, 319.94f, 324.47f, 329.03f, 333.54f, 338.04f, 342.76f, 348.28f};
		float[] color64={  0.05f,  12.49f,  19.87f,  25.76f,  31.02f,  35.91f,  40.59f,  45.18f, 
						  49.76f,  54.51f,  59.78f,   65.2f,  70.02f,  74.37f,  78.53f,  82.51f,
						  86.37f,   90.4f,  94.95f, 100.33f, 106.66f, 123.21f, 134.51f, 140.03f, 
						 144.56f, 148.67f, 152.52f, 156.11f, 159.72f, 163.58f, 168.16f, 173.81f,
						    180f, 185.34f, 189.88f, 194.14f,  198.9f, 204.67f, 210.83f, 217.16f, 
						 224.87f, 242.95f, 259.28f, 265.12f,  269.6f, 273.71f, 277.75f, 281.66f, 
						 285.49f,  289.3f,  293.3f, 297.58f, 302.12f, 306.64f, 311.05f, 315.35f, 
						 319.55f, 323.74f, 327.95f, 332.14f, 336.42f, 341.03f, 346.36f, 352.67f};
		colorHSV[0]=0;
		colorHSV[1]=1;
		colorHSV[2]=1;
		int tmp = 64/colorNum;
		int tmp2 = 32/colorNum;
		for (int i=0; i<colorNum; i++){
			colorHSV[0]=color64[tmp*i];
			colorMap[i] = Color.HSVToColor(colorHSV);
			if (i==0){
				colorHSV[0]=color64[64-tmp2];
			}
			else{
				colorHSV[0]=color64[tmp2+(i-1)*tmp];
			}
			colorMapRef[i] = Color.HSVToColor(colorHSV);
		}
	}

	public int getMapping(int colorCnt) {
		if(colorCnt == 404){
			return Color.WHITE;
		}else if(colorCnt == 505){
			return Color.BLACK;
		}else{
			return colorMap[2*colorCnt];
		}
	}
	
	public int getMappingRef(int colorCnt) {
		if(colorCnt == 404){
			return Color.WHITE;
		}else{
			return colorMapRef[2*colorCnt+1];
		}
	}
}
