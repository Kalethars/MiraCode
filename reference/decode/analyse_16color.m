starttime0=cputime;
filenum=31;
accuracy=zeros(1,filenum);
accuracytopbot=zeros(1,filenum);
for n2=1:filenum
    starttime=cputime;
    tic;
    disp(n2);
    disp('Verkleinern...');
    P=imread(['test',num2str(n2),'.jpg']);
    [x,y,~]=size(P);
    partial=sqrt(x*y/909312);
    P=imresize(P,[round(x/partial) round(y/partial)],'bicubic');
    [x,y,~]=size(P);
    toc;
    tic;
    disp('Kontrast einstellen...');
    RGB=double(P)/255;
    cform2lab=makecform('srgb2lab');
    LAB=applycform(RGB,cform2lab);
    Luminance=LAB(:,:,1)/100    ;
    LAB(:,:,1)=adapthisteq(Luminance,'NumTiles',[50 50],'ClipLimit',0.005)*100;
    cform2srgb=makecform('lab2srgb');
    Pnew=applycform(LAB,cform2srgb);
    imwrite(Pnew,['contrast',num2str(n2),'.jpg']);
    toc;
    tic;
    disp('Grenze rechnnen...');
    c=strel('square',3);
    EdgeColor=rgb2ycbcr(Pnew);
    EdgeColor(:,:,1)=edge(EdgeColor(:,:,1),'canny');
    EdgeColor=ycbcr2rgb(EdgeColor);
    Edge=im2bw(EdgeColor,graythresh(EdgeColor));
    Edge=imdilate(Edge,c);
    imwrite(Edge,['edge',num2str(n2),'.jpg']);
    toc;
    tic;
    disp('Polarisieren...');
    Q=P;
    R=rgb2hsv(Pnew);
    coor_mid=zeros(4,2);
    coor=zeros(4,2);
    leftbound=0.5;
    rightbound=2;
    for i=1:x
        for j=1:y
            if ((R(i,j,3)<0.35 || (R(i,j,3)<0.4 && R(i,j,3)>=0.35 && R(i,j,2)<0.8))) || (R(i,j,2)<0.1 && R(i,j,3)<0.55 && Edge(i,j)==0)
                Q(i,j,1)=0;
                Q(i,j,2)=0;
                Q(i,j,3)=0;
            else
                Q(i,j,1)=255;
                Q(i,j,2)=255;
                Q(i,j,3)=255;
            end
        end
    end
    toc;
    tic;
    disp('Laermpunkte verringern...');
    for i=1:3
        Q=imdilate(imerode(Q,c),c);
    end
    for i=1:3
        Q=imerode(imdilate(Q,c),c);
    end
%     Q=imerode(Q,c);
    imwrite(Q,['black',num2str(n2),'.jpg']);
    toc;
    % figure,imshow(Q);
    % flag2=1;
    tic;
    disp('Ecken suchen...');
%     fid=fopen('a.txt','wt');
    cache=zeros(3,1000,5);
    cachenum=zeros(1,3);
    for i=1:x
        a=zeros(1,6);
        now=0;
        for j=1:y
            if Q(i,j,1)==0 && (now==0 || now==2 || now==4)
                now=now+1;
                a(now)=1;
            elseif Q(i,j,1)==0 && now==6
                now=5;
                a(1)=a(3);
                a(2)=a(4);
                a(3)=a(5);
                a(4)=a(6);
                a(5)=1;
                a(6)=0;
            elseif Q(i,j,1)==255 && (now==1 || now==3)
                now=now+1;
                a(now)=1;
            elseif Q(i,j,1)==255 && now==5 && a(3)>9
                flag=1;
                for k=1:5
                    tmp=a(k)/a(3)*2;
                    if k~=3 && (tmp<leftbound || tmp>rightbound)
                        flag=0;
                        break;
                    end
                end
                if flag==1
                    midy=round(j-a(5)-a(4)-(a(3)+1)/2);
                    lth=(a(1)+a(2)+a(3)+a(4)+a(5))/6;
                    xleft=max(round(i-5*lth),1);
                    xright=min(round(i+5*lth),x);
                    flag2=0;
                    b=zeros(1,6);
                    now2=0;
                    for k=xleft:xright
                        if Q(k,midy,1)==0 && (now2==0 || now2==2 || now2==4)
                            now2=now2+1;
                            b(now2)=1;
                        elseif Q(k,midy,1)==0 && now2==6
                            now2=5;
                            b(1)=b(3);
                            b(2)=b(4);
                            b(3)=b(5);
                            b(4)=b(6);
                            b(5)=1;
                            b(6)=0;
                        elseif Q(k,midy,1)==255 && (now2==1 || now2==3)
                            now2=now2+1;
                            b(now2)=1;
                        elseif Q(k,midy,1)==255 && now2==5 && b(3)>9
                            flag2=1;
                            for l=1:5
                                tmp=b(l)/b(3)*2;
                                if l~=3 && (tmp<leftbound || tmp>rightbound)
                                    flag2=0;
                                    break;
                                end
                            end
                            count=0;
                            for l=k-b(2)-b(3)-b(4)-b(5)+1:k-b(3)-b(4)-b(5)
                                for l2=-2:2
                                    if Q(l,midy+l2,1)==255 && l2~=0
                                        count=count+1;
                                    end
                                end
                            end
                            for l=k-b(4)-b(5)+1:k-b(5)
                                for l2=-2:2
                                    if Q(l,midy+l2,1)==255 && l2~=0
                                        count=count+1;
                                    end
                                end
                            end
                            if count/(b(2)+b(4))/4<0.7
                                flag2=0;
                            end
                            if flag2==1
                                midx=round(k-b(4)-b(5)-(b(3)+1)/2);
                                sumR=0;
                                sumG=0;
                                sumB=0;
                                for l=k-b(2)-b(3)-b(4)-b(5):k-b(3)-b(4)-b(5)+1
                                    sumR=sumR+Pnew(l,midy,1);
                                    sumG=sumG+Pnew(l,midy,2);
                                    sumB=sumB+Pnew(l,midy,3);
                                end
                                for l=k-b(4)-b(5):k-b(5)+1
                                    sumR=sumR+Pnew(l,midy,1);
                                    sumG=sumG+Pnew(l,midy,2);
                                    sumB=sumB+Pnew(l,midy,3);
                                end
                                if sumB<sumR && sumB<sumG
                                    corner=1;
                                elseif sumR<sumG && sumR<sumB
                                    corner=2;
                                elseif sumG<sumR && sumG<sumB
                                    corner=3;
                                end
%                                 disp([midx,midy,corner]);
%                                 disp([i,j]);
                                flag3=0;
                                for l=1:cachenum(corner)
                                    if abs(midx-cache(corner,l,1)/cache(corner,l,3))+abs(midy-cache(corner,l,2)/cache(corner,l,3))<=20
                                        cache(corner,l,1)=cache(corner,l,1)+midx;
                                        cache(corner,l,2)=cache(corner,l,2)+midy;
                                        cache(corner,l,3)=cache(corner,l,3)+1;
                                        cache(corner,l,4)=cache(corner,l,4)+mean(b(1:5))*5/6;
                                        cache(corner,l,5)=cache(corner,l,5)+mean(a(1:5))*5/6;
                                        flag3=1;
                                        break;
                                    end
                                end;
                                if flag3==0
                                    cachenum(corner)=cachenum(corner)+1;
                                    cache(corner,cachenum(corner),1)=midx;
                                    cache(corner,cachenum(corner),2)=midy;
                                    cache(corner,cachenum(corner),3)=1;
                                    cache(corner,cachenum(corner),4)=mean(b(1:5))*5/6;
                                    cache(corner,cachenum(corner),5)=mean(a(1:5))*5/6;
                                end;
                                break;
                            end
                            now2=6;
                            b(now2)=1;
                        elseif Q(k,midy,1)==255 && now2==5
                            now2=6;
                            b(now2)=1;
                        elseif now2>0
                            b(now2)=b(now2)+1;
                        end
                    end
    %                 flag2=0;
    %                 break;
                end
                now=6;
                a(now)=1;
            elseif Q(i,j,1)==255 && now==5
                now=6;
                a(now)=1;
            elseif now>0
                a(now)=a(now)+1;
            end
%             fprintf(fid,'%i\t%i\t%i\t%i\t%i\t%i\t%i\n',j,a(1),a(2),a(3),a(4),a(5),a(6));
        end
    end
%     fclose(fid);
    maxi2=zeros(1,3);
    maxi2now=zeros(1,3);
    sidelen=zeros(4,2);
    for i=1:3
        if cachenum(i)==0
            continue;
        end
        maxi=0;
        for j=1:cachenum(i)
            if maxi<cache(i,j,3)
                if maxi~=0
                    maxi2(i)=maxi;
                    maxi2now(i)=now;
                end
                maxi=cache(i,j,3);
                now=j;
            elseif maxi2(i)<cache(i,j,3)
                maxi2(i)=cache(i,j,3);
                maxi2now(i)=j;
            end
        end
        coor_mid(i,1)=cache(i,now,1)/cache(i,now,3);
        coor_mid(i,2)=cache(i,now,2)/cache(i,now,3);
        sidelen(i,1)=cache(i,now,4)/cache(i,now,3);
        sidelen(i,2)=cache(i,now,5)/cache(i,now,3);
    end
    if maxi2(1)>maxi2(2) && maxi2(1)>maxi2(3)
        fourth=1;
    elseif maxi2(2)>maxi2(1) && maxi2(2)>maxi2(3)
        fourth=2;
    elseif maxi2(3)>maxi2(1) && maxi2(3)>maxi2(2)
        fourth=3;
    end
    coor_mid(4,1)=cache(fourth,maxi2now(fourth),1)/cache(fourth,maxi2now(fourth),3);
    coor_mid(4,2)=cache(fourth,maxi2now(fourth),2)/cache(fourth,maxi2now(fourth),3);
    sidelen(4,1)=cache(fourth,maxi2now(fourth),4)/cache(fourth,maxi2now(fourth),3);
    sidelen(4,2)=cache(fourth,maxi2now(fourth),5)/cache(fourth,maxi2now(fourth),3);
    if fourth==1
        dist1=(coor_mid(1,1)-coor_mid(2,1))^2+(coor_mid(1,2)-coor_mid(2,2))^2;
        dist2=(coor_mid(4,1)-coor_mid(2,1))^2+(coor_mid(4,2)-coor_mid(2,2))^2;
        if dist1>dist2
            tmp=coor_mid(1,1);
            coor_mid(1,1)=coor_mid(4,1);
            coor_mid(4,1)=tmp;
            tmp=coor_mid(1,2);
            coor_mid(1,2)=coor_mid(4,2);
            coor_mid(4,2)=tmp;
            tmp=sidelen(1,1);
            sidelen(1,1)=sidelen(4,1);
            sidelen(4,1)=tmp;
            tmp=sidelen(1,2);
            sidelen(1,2)=sidelen(4,2);
            sidelen(4,2)=tmp;
        end
    elseif fourth==2
        dist1=(coor_mid(2,1)-coor_mid(1,1))^2+(coor_mid(2,2)-coor_mid(1,2))^2;
        dist2=(coor_mid(4,1)-coor_mid(1,1))^2+(coor_mid(4,2)-coor_mid(1,2))^2;
        if dist1>dist2
            tmp=coor_mid(2,1);
            coor_mid(2,1)=coor_mid(4,1);
            coor_mid(4,1)=tmp;
            tmp=coor_mid(2,2);
            coor_mid(2,2)=coor_mid(4,2);
            coor_mid(4,2)=tmp;
            tmp=sidelen(2,1);
            sidelen(2,1)=sidelen(4,1);
            sidelen(4,1)=tmp;
            tmp=sidelen(2,2);
            sidelen(2,2)=sidelen(4,2);
            sidelen(4,2)=tmp;
        end
    elseif fourth==3
        dist1=(coor_mid(3,1)-coor_mid(1,1))^2+(coor_mid(3,2)-coor_mid(1,2))^2;
        dist2=(coor_mid(4,1)-coor_mid(1,1))^2+(coor_mid(4,2)-coor_mid(1,2))^2;
        if dist1>dist2
            tmp=coor_mid(3,1);
            coor_mid(3,1)=coor_mid(4,1);
            coor_mid(4,1)=tmp;
            tmp=coor_mid(3,2);
            coor_mid(3,2)=coor_mid(4,2);
            coor_mid(4,2)=tmp;
            tmp=sidelen(3,2);
            sidelen(3,1)=sidelen(4,1);
            sidelen(4,1)=tmp;
            tmp=sidelen(3,2);
            sidelen(3,2)=sidelen(4,2);
            sidelen(4,2)=tmp;
        end
    end
%     for i=1:3
%         if cachenum(i)==0
%             for j=1:4
%                 if j==5-i
%                     coor_mid(i,1)=coor_mid(i,1)-coor_mid(j,1);
%                     coor_mid(i,2)=coor_mid(i,2)-coor_mid(j,2);
%                 elseif j~=i
%                     coor_mid(i,1)=coor_mid(i,1)+coor_mid(j,1);
%                     coor_mid(i,2)=coor_mid(i,2)+coor_mid(j,2);
%                 end
%             end
%         end
%     end
    toc;
    tic;
    disp('Ecken verbessern...');
    xtmp1=round(coor_mid(3,1)-(coor_mid(3,1)-coor_mid(1,1))*68/65);
    ytmp1=round(coor_mid(3,2)-(coor_mid(3,2)-coor_mid(1,2))*68/65);
    xtmp2=round(coor_mid(2,1)-(coor_mid(2,1)-coor_mid(1,1))*42/39);
    ytmp2=round(coor_mid(2,2)-(coor_mid(2,2)-coor_mid(1,2))*42/39);
    coor(1,1)=round(xtmp1+xtmp2-coor_mid(1,1));
    coor(1,2)=round(ytmp1+ytmp2-coor_mid(1,2));
    xtmp1=round(coor_mid(4,1)-(coor_mid(4,1)-coor_mid(2,1))*68/65);
    ytmp1=round(coor_mid(4,2)-(coor_mid(4,2)-coor_mid(2,2))*68/65);
    xtmp2=round(coor_mid(1,1)-(coor_mid(1,1)-coor_mid(2,1))*42/39);
    ytmp2=round(coor_mid(1,2)-(coor_mid(1,2)-coor_mid(2,2))*42/39);
    coor(2,1)=round(xtmp1+xtmp2-coor_mid(2,1));
    coor(2,2)=round(ytmp1+ytmp2-coor_mid(2,2));
    xtmp1=round(coor_mid(1,1)-(coor_mid(1,1)-coor_mid(3,1))*68/65);
    ytmp1=round(coor_mid(1,2)-(coor_mid(1,2)-coor_mid(3,2))*68/65);
    xtmp2=round(coor_mid(4,1)-(coor_mid(4,1)-coor_mid(3,1))*42/39);
    ytmp2=round(coor_mid(4,2)-(coor_mid(4,2)-coor_mid(3,2))*42/39);
    coor(3,1)=round(xtmp1+xtmp2-coor_mid(3,1));
    coor(3,2)=round(ytmp1+ytmp2-coor_mid(3,2));
    xtmp1=round(coor_mid(2,1)-(coor_mid(2,1)-coor_mid(4,1))*68/65);
    ytmp1=round(coor_mid(2,2)-(coor_mid(2,2)-coor_mid(4,2))*68/65);
    xtmp2=round(coor_mid(3,1)-(coor_mid(3,1)-coor_mid(4,1))*42/39);
    ytmp2=round(coor_mid(3,2)-(coor_mid(3,2)-coor_mid(4,2))*42/39);
    coor(4,1)=round(xtmp1+xtmp2-coor_mid(4,1));
    coor(4,2)=round(ytmp1+ytmp2-coor_mid(4,2));
%     disp(coor);
%     sidelen=sqrt((coor(1,1)-coor(2,1))*(coor(1,1)-coor(2,1))+(coor(1,2)-coor(2,2))*(coor(1,2)-coor(2,2)))/39;
%     sidelen=max(sqrt((coor(2,1)-coor(4,1))*(coor(2,1)-coor(4,1))+(coor(2,2)-coor(4,2))*(coor(2,2)-coor(4,2)))/65,sidelen);
%     sidelen=max(sqrt((coor(4,1)-coor(3,1))*(coor(4,1)-coor(3,1))+(coor(4,2)-coor(3,2))*(coor(4,2)-coor(3,2)))/39,sidelen);
%     sidelen=max(sqrt((coor(3,1)-coor(1,1))*(coor(3,1)-coor(1,1))+(coor(3,2)-coor(1,2))*(coor(3,2)-coor(1,2)))/65,sidelen);
%     disp(sidelen);
    for i=1:4
        mini=10000;
        xleft=max(round(coor(i,1)-sidelen(i,1)),1);
        xright=min(round(coor(i,1)+sidelen(i,1)),x);
        yleft=max(round(coor(i,2)-sidelen(i,2)),1);
        yright=min(round(coor(i,2)+sidelen(i,2)),y);
        searchrange=round(max(sidelen(i,1),sidelen(i,2))/2);
        prevx=coor(i,1);
        prevy=coor(i,2);
        for j=xleft:xright
            for k=yleft:yright
                if Q(j,k,1)==255 || (j-coor_mid(i,1))^2+(k-coor_mid(i,2))^2>12*sidelen(i,1)^2+12*sidelen(i,2)^2 || ...
                    int64(Q(j-1,k,1))+int64(Q(j,k+1,1))+int64(Q(j+1,k,1))+int64(Q(j,k-1,1))<=255
                    continue;
                end
%                 if Q(j,k,1)==255 || (j-coor_mid(i,1))^2+(k-coor_mid(i,2))^2>11*sidelen(i,1)^2+11*sidelen(i,2)^2 || ...
%                     (Edge(j,k)==0 && int64(Q(j-1,k,1))+int64(Q(j,k+1,1))+int64(Q(j+1,k,1))+int64(Q(j,k-1,1))<=255)
%                     continue;
%                 end
                count=0;
%                 if (Edge(j,k)==1 || Edge(j-1,k-1)==1 || Edge(j-1,k)==1 || Edge(j-1,k+1)==1 || Edge(j,k-1)==1 ||...
%                          Edge(j,k+1)==1 || Edge(j+1,k-1)==1 || Edge(j+1,k)==1 || Edge(j+1,k+1)==1) &&...
%                     int64(Q(j-1,k,1))+int64(Q(j,k+1,1))+int64(Q(j+1,k,1))+int64(Q(j,k-1,1))>=510
%                         (j-coor_mid(i,1))^2+(k-coor_mid(i,2))^2<=10*sidelen(i,1)^2+10*sidelen(i,2)^2 &&...
%                         (j-coor_mid(i,1))^2+(k-coor_mid(i,2))^2>=7*sidelen(i,1)^2+7*sidelen(i,2)^2
%                     count=-1000;
%                 end
                for j2=-searchrange:searchrange
                    for k2=-searchrange:searchrange
                        if j+j2<=0 || j+j2>x || k+k2<=0 || k+k2>y
                            count=count+1;
                            continue;
                        end
                        if Q(j+j2,k+k2,1)==0
                            count=count+1;
                        end
                    end
                end
                if count<mini
                    mini=count;
                    minx=j;
                    miny=k;
                end
            end
        end
        if mini<10000
            coor(i,1)=minx;
            coor(i,2)=miny;
        end
    end
%     disp(coor);
%     istop=zeros(1,4);
%     isbot=zeros(1,4);
%     isleft=zeros(1,4);
%     isright=zeros(1,4);
%     for i=1:4
%         for j=1:4
%             if coor(i,1)>coor(j,1)
%                 isbot(i)=isbot(i)+1;
%             elseif coor(i,1)<coor(j,1)
%                 istop(i)=istop(i)+1;
%             end
%             if coor(i,2)>coor(j,2)
%                 isright(i)=isright(i)+1;
%             elseif coor(i,2)<coor(j,2)
%                 isleft(i)=isleft(i)+1;
%             end
%         end
%     end
%     corr=1;
%     for i=1:4
%         if istop(i)>1
%             coor(i,1)=coor(i,1)+corr;
%         end
%         if isbot(i)>1
%             coor(i,1)=coor(i,1)-corr;
%         end
%         if isleft(i)>1
%             coor(i,2)=coor(i,2)+corr;
%         end
%         if isright(i)>1
%             coor(i,2)=coor(i,2)-corr;
%         end
%     end
    for i=1:4
        tmp=coor(i,1);
        coor(i,1)=coor(i,2);
        coor(i,2)=tmp;
    end
    toc;
    tic;
    disp('Perspective freistellen...');
    tform=maketform('projective',coor,[1 1;720 1;1 1136;720 1136]);
    P2=imtransform(P,tform,'XData',[1 720],'YData',[1 1136]);
    imwrite(P2,['result',num2str(n2),'.jpg']);
    toc;
    tic;
    disp('Farton der Referenzfarben rechnen...');
    reflen=4;
    collen=2;
    reftable=[1 9 4 12 7 15 10 2 13 5 16 8 3 11 6 14 9 1 12 4 15 7 2 10 5 13 8 16 11 3 14 6];
    refhue=zeros(1,16);
    refhuetop=zeros(1,16);
    refhuebot=zeros(1,16);
    sumcol=zeros(16,3);
    sumcoltop=zeros(16,3);
    sumcolbot=zeros(16,3);
    now=0;
    for i=1:6
        now=now+1;
        sumR=0;
        sumG=0;
        sumB=0;
        for j=65-reflen:64+reflen
            for k=i*80+81-reflen:i*80+80+reflen
                for l=1:3
                    sumcol(reftable(now),l)=sumcol(reftable(now),l)+int64(P2(j,k,l));
                    sumcoltop(reftable(now),l)=sumcoltop(reftable(now),l)+int64(P2(j,k,l));
                end
            end
        end
    end
    for i=1:10
        now=now+1;
        sumR=0;
        sumG=0;
        sumB=0;
        for j=i*80+129-reflen:i*80+128+reflen
            for k=657-reflen:656+reflen
                for l=1:3
                    sumcol(reftable(now),l)=sumcol(reftable(now),l)+int64(P2(j,k,l));
                    if i<5
                        sumcoltop(reftable(now),l)=sumcoltop(reftable(now),l)+int64(P2(j,k,l));
                    else
                        sumcolbot(reftable(now),l)=sumcolbot(reftable(now),l)+int64(P2(j,k,l));
                    end
                end
            end
        end
    end
    for i=1:6
        now=now+1;
        sumR=0;
        sumG=0;
        sumB=0;
        for j=1073-reflen:1072+reflen
            for k=(7-i)*80+81-reflen:(7-i)*80+80+reflen
                for l=1:3
                    sumcol(reftable(now),l)=sumcol(reftable(now),l)+int64(P2(j,k,l));
                    sumcolbot(reftable(now),l)=sumcolbot(reftable(now),l)+int64(P2(j,k,l));
                end
            end
        end
    end
    for i=1:10
        now=now+1;
        sumR=0;
        sumG=0;
        sumB=0;
        for j=(11-i)*80+129-reflen:(11-i)*80+128+reflen
            for k=65-reflen:64+reflen
                for l=1:3
                    sumcol(reftable(now),l)=sumcol(reftable(now),l)+int64(P2(j,k,l));
                    if i>4
                        sumcoltop(reftable(now),l)=sumcoltop(reftable(now),l)+int64(P2(j,k,l));
                    else
                        sumcolbot(reftable(now),l)=sumcolbot(reftable(now),l)+int64(P2(j,k,l));
                    end
                end
            end
        end
    end
    for i=1:16
        for j=1:3
            sumcol(i,j)=double(sumcol(i,j))/8/reflen/reflen;
            sumcoltop(i,j)=double(sumcoltop(i,j))/4/reflen/reflen;
            sumcolbot(i,j)=double(sumcolbot(i,j))/4/reflen/reflen;
        end
        [refhue(i),~,~]=rgb2hsv(uint8([sumcol(i,1),sumcol(i,2),sumcol(i,3)]));
        refhue(i)=refhue(i)*360;
        [refhuetop(i),~,~]=rgb2hsv(uint8([sumcoltop(i,1),sumcoltop(i,2),sumcoltop(i,3)]));
        refhuetop(i)=refhuetop(i)*360;
        [refhuebot(i),ss,vv]=rgb2hsv(uint8([sumcolbot(i,1),sumcolbot(i,2),sumcolbot(i,3)]));
        refhuebot(i)=refhuebot(i)*360;
    end
    for i=1:3
        for j=1:16
            if refhue(j)>refhue(mod(j,16)+1) && refhue(j)-refhue(mod(j,16)+1)<180
                tmp=refhue(j);
                refhue(j)=refhue(mod(j,16)+1);
                refhue(mod(j,16)+1)=tmp;
            end
            if refhuetop(j)>refhuetop(mod(j,16)+1) && refhuetop(j)-refhuetop(mod(j,16)+1)<180
                tmp=refhuetop(j);
                refhuetop(j)=refhuetop(mod(j,16)+1);
                refhuetop(mod(j,16)+1)=tmp;
            end
            if refhuebot(j)>refhuebot(mod(j,16)+1) && refhuebot(j)-refhuebot(mod(j,16)+1)<180
                tmp=refhuebot(j);
                refhuebot(j)=refhuebot(mod(j,16)+1);
                refhuebot(mod(j,16)+1)=tmp;
            end
        end
    end
    toc;
    tic;
    disp('Farben erkennen...');
    neinpic=rgb2hsv(P2);
    for i=1:1136
        for j=1:720
            neinpic(i,j,1)=0;
            neinpic(i,j,2)=0;
            neinpic(i,j,3)=1;
        end
    end
    load 'table.txt'
    count=0;
    for i=1:59
        for j=1:33
            sumcol=zeros(1,3);
            for x=i*16+89-collen:i*16+88+collen
                for y=j*16+89-collen:j*16+88+collen
                    for k=1:3
                        sumcol(k)=sumcol(k)+int64(P2(x,y,k));
                    end
                end
            end
            for k=1:3
                sumcol(k)=double(sumcol(k))/4/collen/collen;
            end
            [hh,ss,vv]=rgb2hsv(uint8([sumcol(1),sumcol(2),sumcol(3)]));
            hh=hh*360;
            for k=1:16
                lefthue=refhue(mod(k+14,16)+1);
                righthue=refhue(k);
                if (lefthue<hh && hh<righthue) || ((hh>lefthue || hh<righthue) && lefthue-righthue>180)
                    now=k;
                    break;
                end
            end
            if now==table(i,j)
                count=count+1;
            else
                for x=i*16+81:i*16+96
                    for y=j*16+81:j*16+96
                        neinpic(x,y,1)=hh/360;
                        neinpic(x,y,2)=1;
                        neinpic(x,y,3)=1;
                    end
                end
            end
        end
    end
    imwrite(hsv2rgb(neinpic),['nein',num2str(n2),'.jpg']);
    toc;
    accuracy(n2)=double(count)/59/33*100;
    disp([num2str(accuracy(n2)),'%']);
%     tic;
%     disp('Farben erkennen (top-bot)...');
%     for i=1:1136
%         for j=1:720
%             neinpic(i,j,1)=0;
%             neinpic(i,j,2)=0;
%             neinpic(i,j,3)=1;
%         end
%     end
%     count=0;
%     for i=1:59
%         for j=1:33
%             sumcol=zeros(1,3);
%             for x=i*16+89-collen:i*16+88+collen
%                 for y=j*16+89-collen:j*16+88+collen
%                     for k=1:3
%                         sumcol(k)=sumcol(k)+int64(P2(x,y,k));
%                     end
%                 end
%             end
%             for k=1:3
%                 sumcol(k)=double(sumcol(k))/4/collen/collen;
%             end
%             [hh,ss,vv]=rgb2hsv(uint8([sumcol(1),sumcol(2),sumcol(3)]));
%             hh=hh*360;
%             for k=1:16
%                 if i<30
%                     lefthue=refhuetop(mod(k+14,16)+1);
%                     righthue=refhuetop(k);
%                 else
%                     lefthue=refhuebot(mod(k+14,16)+1);
%                     righthue=refhuebot(k);
%                 end
%                 if (lefthue<hh && hh<righthue) || ((hh>lefthue || hh<righthue) && lefthue-righthue>180)
%                     now=k;
%                     break;
%                 end
%             end
%             if now==table(i,j)
%                 count=count+1;
%             else
%                 for x=i*16+81:i*16+96
%                     for y=j*16+81:j*16+96
%                         neinpic(x,y,1)=hh/360;
%                         neinpic(x,y,2)=1;
%                         neinpic(x,y,3)=1;
%                     end
%                 end
%             end
%         end
%     end
%     imwrite(hsv2rgb(neinpic),['neintopbot',num2str(n2),'.jpg']);
%     toc;
%     accuracytopbot(n2)=double(count)/59/33*100;
%     disp([num2str(accuracytopbot(n2)),'%']);
    disp(['Zeit verbraucht: ',num2str(cputime-starttime)]);
end
disp(['Insgesamt Zeit: ',num2str(cputime-starttime0)]);