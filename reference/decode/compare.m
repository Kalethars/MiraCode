load 'table2.txt'
load 'mask.txt'
ref2=[359,8,34,55,73,98,123,145,165,188,217,240,264,289,312,334];
count=0;
corr=zeros(59,33);
for i=1:15
    for j=1:33
        for k=1:16
            if (table2(i,j)>ref2(k) && table2(i,j)<ref2(mod(k,16)+1)) || (ref2(k)-ref2(mod(k,16)+1)>180 && ((table2(i,j)>ref2(k) || table2(i,j)<ref2(mod(k,16)+1))))
                if k==table(i,j)
                    count=count+1;
                end
                corr(i,j)=k;
                break;
            end
        end
    end
end
disp([num2str(count/33/15*100),'%']);
count=0;
for i=16:30
    for j=1:33
        for k=1:16
            if (table2(i,j)>ref2(k) && table2(i,j)<ref2(mod(k,16)+1)) || (ref2(k)-ref2(mod(k,16)+1)>180 && ((table2(i,j)>ref2(k) || table2(i,j)<ref2(mod(k,16)+1))))
                if k==table(i,j)
                    count=count+1;
                end
                corr(i,j)=k;
                break;
            end
        end
    end
end
disp([num2str(count/33/15*100),'%']);
count=0;
for i=31:45
    for j=1:33
        for k=1:16
            if (table2(i,j)>ref2(k) && table2(i,j)<ref2(mod(k,16)+1)) || (ref2(k)-ref2(mod(k,16)+1)>180 && ((table2(i,j)>ref2(k) || table2(i,j)<ref2(mod(k,16)+1))))
                if k==table(i,j)
                    count=count+1;
                end
                corr(i,j)=k;
                break;
            end
        end
    end
end
disp([num2str(count/33/15*100),'%']);
count=0;
for i=46:59
    for j=1:33
        for k=1:16
            if (table2(i,j)>ref2(k) && table2(i,j)<ref2(mod(k,16)+1)) || (ref2(k)-ref2(mod(k,16)+1)>180 && ((table2(i,j)>ref2(k) || table2(i,j)<ref2(mod(k,16)+1))))
                if k==table(i,j)
                    count=count+1;
                end
                corr(i,j)=k;
                break;
            end
        end
    end
end
disp([num2str(count/33/14*100),'%']);
for i=1:59
    for j=1:32
        corr(i,j)=mod(corr(i,j)+22-mask(i,j),16);
    end
end
byte=zeros(59,16);
for i=1:59
    for j=1:16
        byte(i,j)=corr(i,j*2-1)*16+corr(i,j*2);
    end
end
s='[';
for i=1:15
    for j=1:12
        if i*j<240
            s=[s,num2str(byte(i,j)),', '];
        end
    end
end
for i=1:15
    for j=13:16
        if i*j<240
            s=[s,num2str(byte(i,j)),', '];
        else
            s=[s,num2str(byte(i,j)),']'];
        end
    end
end