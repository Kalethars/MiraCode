load 'table.txt'
for n=2:7
    count=0;
    P=imread(['test',num2str(n),'.jpg']);
    ref=zeros(1,16);
    reflen=4;
    collen=2;
    for i=1:16
        sum=zeros(1,3);
        for x=i*32-15-reflen:i*32-16+reflen
            for y=17-reflen:16+reflen
                for z=1:3
                    sum(z)=sum(z)+int64(P(x,y,z));
                end
            end
        end
        for x=i*32-15-reflen:i*32-16+reflen
            for y=641-reflen:640+reflen
                for z=1:3
                    sum(z)=sum(z)+int64(P(x,y,z));
                end
            end
        end
        sum=sum/reflen/reflen/8;
        [h,~,~]=rgb2hsv(uint8(sum));
        ref(i)=h*360;
    end
    hue=zeros(59,33);
    for i=1:59
        for j=1:33
            sum=zeros(1,3);
            for x=i*16-7-collen:i*16-8+collen
                for y=j*16+57-collen:j*16+56+collen
                    for z=1:3
                        sum(z)=sum(z)+int64(P(x,y,z));
                    end
                end
            end
            sum=sum/collen/collen/4;
            [h,~,~]=rgb2hsv(uint8(sum));
            hue(i,j)=h*360;
            for k=1:16
                if (hue(i,j)>ref(k) && hue(i,j)<ref(mod(k,16)+1)) || (ref(k)-ref(mod(k,16)+1)>180 && ((hue(i,j)>ref(k) || hue(i,j)<ref(mod(k,16)+1))))
                    if k==table(i,j)
                        count=count+1;
                    end
                    break;
                end
            end
        end
    end
    disp([num2str(count/33/59*100),'%']);
end