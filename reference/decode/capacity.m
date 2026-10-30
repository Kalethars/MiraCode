% for i=1:29
%     for j=i+1:30
%         if acc(i)<acc(j)
%             tmp=acc(i);
%             acc(i)=acc(j);
%             acc(j)=tmp;
%         end
%     end
% end
cap=zeros(3,30);
for j=1:3
    for i=1:30
        cap(j,i)=(2*(acc(j,i)/100)^(8/log2(i+2))-1)*1888*log2(i+2)/8;
    end
end
plot(3:32,cap(1,:),'k',3:32,cap(2,:),'r',3:32,cap(3,:),'b')