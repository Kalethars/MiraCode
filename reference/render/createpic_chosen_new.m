P=zeros(1184,768,3);
now=0;
pcount=0;
roll=0;
refcount=0;
refnow=0;
a=[0.05, 31.02, 49.76, 70.02, 86.37, 106.66, 144.56, 159.72, 180, 198.9, 224.87, 269.6, 285.49, 302.12, 319.55, 336.42];
b=[0.05, 19.87, 31.02, 40.59, 49.76, 59.78, 70.02, 78.53, 86.37, 94.95, 106.66, 134.51, 144.56, 152.52, 159.72, 168.16, 180, 189.88, 198.9, 210.83, 224.87, 259.28, 269.6, 277.75, 285.49, 293.3, 302.12, 311.05, 319.55, 327.95, 336.42, 346.36];
load 'table.txt'
% fid=fopen('table_new.txt','wt');
for i=1:1184
    for j=1:768
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
for i=1065:1160
    for j=25:120
        P(i,j,1)=0;
        P(i,j,2)=0;
        P(i,j,3)=0;
    end
end
for i=25:120
    for j=649:744
        P(i,j,1)=0;
        P(i,j,2)=0;
        P(i,j,3)=0;
    end
end
for i=1065:1160
    for j=649:744
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
    for j=665+corr:728-corr
        P(i,j,1)=1/2;
        P(i,j,2)=1;
        P(i,j,3)=1;
    end
end
for i=1081+corr:1144-corr
    for j=41+corr:104-corr
        P(i,j,1)=5/6;
        P(i,j,2)=1;
        P(i,j,3)=1;
    end
end
for i=1081+corr:1144-corr
    for j=665+corr:728-corr
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
    for j=681-corr:712+corr
        P(i,j,1)=0;
        P(i,j,2)=0;
        P(i,j,3)=0;
    end
end
for i=1097-corr:1128+corr
    for j=57-corr:88+corr
        P(i,j,1)=0;
        P(i,j,2)=0;
        P(i,j,3)=0;
    end
end
for i=1097-corr:1128+corr
    for j=681-corr:712+corr
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
for i=1:6
    for k=49:96
        for l=i*80+81:i*80+128
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
    for k=i*80+129:i*80+176
        for l=673:720
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
for i=1:6
    for k=1089:1136
        for l=(7-i)*80+81:(7-i)*80+128
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
    for k=(11-i)*80+129:(11-i)*80+176
        for l=49:96
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
for i=1:59
    for j=1:33
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
        for k=i*16+105:i*16+120
            for l=j*16+105:j*16+120
%                 P(k,l,1)=c(mod(now+1,16)+1)/360;
                P(k,l,1)=a(table(i,j))/360;
                P(k,l,2)=1;
                P(k,l,3)=1;
%                 if flag==0
%                     if j<33
%                         fprintf(fid,'%i\t',cc(mod(now+1,16)+1));
%                     else
%                         fprintf(fid,'%i\r\n',cc(mod(now+1,16)+1));
%                     end
%                     flag=1;
%                 end
            end
        end
%         now=mod(now+1,16);
    end
end
% fclose(fid);
imwrite(hsv2rgb(P),'16color_new.bmp');