P=zeros(1024,1792,3);
now=0;
pcount=0;
roll=0;
refcount=0;
refnow=0;
load 'colorarray.txt'
a=zeros(1,16);
b=zeros(1,32);
for i=1:16
    a(i)=colorarray(14,2*i-1);
end
for i=1:32
    b(i)=colorarray(14,i);
end
% a=[355.56, 28.76, 49.15, 70.97, 86.36, 105.22, 143.64, 159.45, 180, 198.36, 222.11, 266.72, 281.45, 296.36, 314.67, 332.74];
% b=[355.56, 16.59, 28.76, 39.02, 49.15, 60.37, 70.97, 79.0, 86.36, 94.38, 105.22, 132.86, 143.64, 151.96, 159.45, 167.94, 180, 189.74, 198.36, 209.67, 222.11, 254.52, 266.72, 274.3, 281.45, 288.43, 296.36, 305.54, 314.67, 323.68, 332.74, 342.47];
% load 'table.txt'
% fid=fopen('table.txt','wt');
P2=imread('Penguin_2.bmp');
for i=1:1024
    for j=1:1792
        P(i,j,1)=0;
        P(i,j,2)=0;
        P(i,j,3)=1;
    end
end
for i=25:120
    for j=25:120
        P(i,j,1)=0;
        P(i,j,2)=0;
        P(i,j,3)=0;
    end
end
for i=905:1000
    for j=25:120
        P(i,j,1)=0;
        P(i,j,2)=0;
        P(i,j,3)=0;
    end
end
for i=25:120
    for j=1673:1768
        P(i,j,1)=0;
        P(i,j,2)=0;
        P(i,j,3)=0;
    end
end
for i=905:1000
    for j=1673:1768
        P(i,j,1)=0;
        P(i,j,2)=0;
        P(i,j,3)=0;
    end
end
% 四角块外围↑
corr=1;
for i=41+corr:104-corr
    for j=41+corr:104-corr
        P(i,j,1)=1/6;
        P(i,j,2)=1;
        P(i,j,3)=1;
    end
end
for i=41+corr:104-corr
    for j=1689+corr:1752-corr
        P(i,j,1)=5/6;
        P(i,j,2)=1;
        P(i,j,3)=1;
    end
end
for i=921+corr:984-corr
    for j=41+corr:104-corr
        P(i,j,1)=1/2;
        P(i,j,2)=1;
        P(i,j,3)=1;
    end
end
for i=921+corr:984-corr
    for j=1689+corr:1752-corr
        P(i,j,1)=1/6;
        P(i,j,2)=0;
        P(i,j,3)=1;
    end
end
% 四角块中围↑
for i=57-corr:88+corr
    for j=57-corr:88+corr
        P(i,j,1)=0;
        P(i,j,2)=0;
        P(i,j,3)=0;
    end
end
for i=57-corr:88+corr
    for j=1705-corr:1736+corr
        P(i,j,1)=0;
        P(i,j,2)=0;
        P(i,j,3)=0;
    end
end
for i=937-corr:968+corr
    for j=57-corr:88+corr
        P(i,j,1)=0;
        P(i,j,2)=0;
        P(i,j,3)=0;
    end
end
for i=937-corr:968+corr
    for j=1705-corr:1736+corr
        P(i,j,1)=0;
        P(i,j,2)=0;
        P(i,j,3)=0;
    end
end
% 四角块内围↑
% for i=1:16
%     for k=33:48
%         for l=i*32+97:i*32+112
%             P(k,l,1)=0;
%             P(k,l,2)=0;
%             P(k,l,3)=0;
%         end
%     end
% end
% for i=1:16
%     for k=1121:1136
%         for l=i*32+97:i*32+112
%             P(k,l,1)=0;
%             P(k,l,2)=0;
%             P(k,l,3)=0;
%         end
%     end
% end
% for i=1:29
%     for k=i*32+97:i*32+112
%         for l=33:48
%             P(k,l,1)=0;
%             P(k,l,2)=0;
%             P(k,l,3)=0;
%         end
%     end
% end
% for i=1:29
%     for k=i*32+97:i*32+112
%         for l=705:720
%             P(k,l,1)=0;
%             P(k,l,2)=0;
%             P(k,l,3)=0;
%         end
%     end
% end
% timing reference↑
p1=8;
p2=11;
for i=1:22
    for k=53:92
        for l=i*64+141:i*64+180
            P(k,l,1)=b(2*(refnow+1))/360;
            P(k,l,2)=1;
            P(k,l,3)=1;
        end
    end
    if refcount==0
        refnow=mod(refnow+p1,16);
        refcount=1;
    else
        refnow=mod(refnow+p2,16);
        refcount=0;
    end
end
for i=1:10
    for k=i*64+141:i*64+180
        for l=1701:1740
            P(k,l,1)=b(2*(refnow+1))/360;
            P(k,l,2)=1;
            P(k,l,3)=1;
        end
    end
    if refcount==0
        refnow=mod(refnow+p1,16);
        refcount=1;
    else
        refnow=mod(refnow+p2,16);
        refcount=0;
    end
end
for i=1:22
    for k=933:972
        for l=(23-i)*64+141:(23-i)*64+180
            P(k,l,1)=b(2*(refnow+1))/360;
            P(k,l,2)=1;
            P(k,l,3)=1;
        end
    end
    if refcount==0
        refnow=mod(refnow+p1,16);
        refcount=1;
    else
        refnow=mod(refnow+p2,16);
        refcount=0;
    end
end
for i=1:10
    for k=(11-i)*64+141:(11-i)*64+180
        for l=53:92
            P(k,l,1)=b(2*(refnow+1))/360;
            P(k,l,2)=1;
            P(k,l,3)=1;
        end
    end
    if refcount==0
        refnow=mod(refnow+p1,16);
        refcount=1;
    else
        refnow=mod(refnow+p2,16);
        refcount=0;
    end
end
% 参考色↑
% for i=1:49
%     for j=1:97
%         flag=0;
%         if now==0
%             pcount=0;
%             bool=zeros(1,16);
%             c=zeros(1,16);
%             cc=zeros(1,16);
%             for k=1:16
%                 rd=random('unid',16);
%                 for l=1:rd
%                     pcount=mod(pcount+1,16);
%                     while bool(pcount+1)==1
%                         pcount=mod(pcount+1,16);
%                     end
%                 end
%                 bool(pcount+1)=1; 
%                 c(k)=a(pcount+1);
%                 cc(k)=pcount+1;
%             end
%         end
%         for k=i*16+105:i*16+120
%             for l=j*16+105:j*16+120
%                 P(k,l,1)=c(mod(now+1,16)+1)/360;
%                 P(k,l,1)=a(table(i,j))/360;
%                 P(k,l,2)=1;
%                 P(k,l,3)=1;
%                 if flag==0
%                     if j<97
%                         fprintf(fid,'%i\t',cc(mod(now+1,16)+1));
%                     else
%                         fprintf(fid,'%i\r\n',cc(mod(now+1,16)+1));
%                     end
%                     flag=1;
%                 end
%             end
%         end
%         now=mod(now+1,16);
%     end
% end
% fclose(fid);
P=hsv2rgb(P);        
P(121:904,121:1672,:)=double(P2(:,:,:))/255;
imwrite(P,'IMG4.bmp');