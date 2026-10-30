P=imread('Maldives.jpg');
load 'colorarray.txt'
[x,y,~]=size(P);
len=16;
% P2=zeros(x,y,3);
% P2(:,:,1)=215;
% P2(:,:,2)=170;
% P2(:,:,3)=50;
% P=uint8(0.8*double(P)+0.2*P2);
f=fopen('plaintext.txt','r');
ptext=fread(f);
fclose(f);
bound=ceil(length(ptext)*8/19);
pt=zeros(1,798);
for i=1:length(ptext)
    tmp=abs(ptext(i));
    for j=8*i:-1:8*(i-1)+1
        pt(j)=mod(tmp,2);
        tmp=floor(tmp/2);
    end
end
tri=zeros(1,512);
for i=1:bound
    tmp=pt((i-1)*19+1);
    for j=(i-1)*19+2:i*19
        tmp=tmp*2+pt(j);
    end
    for j=12*i:-1:12*(i-1)+1
        tri(j)=mod(tmp,3);
        tmp=floor(tmp/3);
    end
end
f=fopen('table.txt','w');
colornum=15;
disp(colornum);
Q=zeros(x,y,3);
len2=16;
table=zeros(ceil(x/len),ceil(y/len));
for i=1:ceil(x/len)
    for j=1:ceil(y/len)
        sum=zeros(1,3);
        xx=min(x,(i-1)*len+len)-(i-1)*len;
        yy=min(y,(j-1)*len+len)-(j-1)*len;
        for k=(i-1)*len+1:min(x,(i-1)*len+len)
            for l=(j-1)*len+1:min(y,(j-1)*len+len)
                for m=1:3
                    sum(m)=sum(m)+int64(P(k,l,m));
                end
            end
        end
        [h,s,v]=rgb2hsv(uint8(sum/xx/yy));
        h=h*360;
        for k=1:colornum
            if k==1
                lefthue=colorarray(colornum-2,2*colornum);
            else
                lefthue=colorarray(colornum-2,2*k-2);
            end
            righthue=colorarray(colornum-2,2*k);
            if (lefthue<h && h<righthue) || ((h>lefthue || h<righthue) && lefthue-righthue>180)
                now=k;
                break;
            end
        end
        pos=(ceil(i/3)-1)*32+ceil(j/3);
        if i==49
            pos=pos-32;
        end
        if j==97
            pos=pos-1;
        end
        if mod(now,3)==0
            if tri(pos)==1
                now=now+1;
            elseif tri(pos)==2
                now=now-1;
            end
        elseif mod(now,3)==1
            if tri(pos)==0
                now=now-1;
            elseif tri(pos)==2
                now=now+1;
            end
        else
            if tri(pos)==0
                now=now+1;
            elseif tri(pos)==1
                now=now-1;
            end
        end
        now=mod(now+colornum-1,colornum)+1;
        table(i,j)=now;
        fprintf(f,'%i\t',now);
    end
    fprintf(f,'\r\n');
end
% for i=1:floor(ceil(x/len)/3)
%     for j=1:floor(ceil(y/len)/3)
%         table((i-1)*3+1,(j-1)*3+1)=0.8*table((i-1)*3+1,(j-1)*3+1)+0.2*table((i-1)*3+2,(j-1)*3+2);
%         table((i-1)*3+1,(j-1)*3+2)=0.6*table((i-1)*3+1,(j-1)*3+2)+0.4*table((i-1)*3+2,(j-1)*3+2);
%         table((i-1)*3+1,(j-1)*3+3)=0.8*table((i-1)*3+1,(j-1)*3+3)+0.2*table((i-1)*3+2,(j-1)*3+2);
%         table((i-1)*3+2,(j-1)*3+1)=0.6*table((i-1)*3+2,(j-1)*3+1)+0.4*table((i-1)*3+2,(j-1)*3+2);
%         table((i-1)*3+2,(j-1)*3+3)=0.6*table((i-1)*3+2,(j-1)*3+3)+0.4*table((i-1)*3+2,(j-1)*3+2);
%         table((i-1)*3+3,(j-1)*3+1)=0.8*table((i-1)*3+3,(j-1)*3+1)+0.2*table((i-1)*3+2,(j-1)*3+2);
%         table((i-1)*3+3,(j-1)*3+2)=0.6*table((i-1)*3+3,(j-1)*3+2)+0.4*table((i-1)*3+2,(j-1)*3+2);
%         table((i-1)*3+3,(j-1)*3+3)=0.8*table((i-1)*3+3,(j-1)*3+3)+0.2*table((i-1)*3+2,(j-1)*3+2);
%     end
% end
P=rgb2hsv(P);
xx=len2/len*x;
yy=len2/len*y;
for i=1:xx
    for j=1:yy
        ii=ceil(i/len2);
        jj=ceil(j/len2);
        Q(i,j,1)=colorarray(colornum-2,2*table(ii,jj)-1)/360;
        Q(i,j,2)=max(0.5,P(i,j,2));
        Q(i,j,3)=max(0.5,P(i,j,3));
    end
end
imwrite(hsv2rgb(Q),'Maldives_1.bmp');
fclose(f);