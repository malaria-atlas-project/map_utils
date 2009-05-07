      SUBROUTINE multiinc(x,ind,nxi,nxj,nxk)
cf2py intent(hide) nxi,nxj,nxk
cf2py intent(inplace) x
cf2py threadsafe
      INTEGER x(nxi,nxj,nxk), ind(nxi,nxj), nxi, nxj
      INTEGER nxk, i, j
      
      do i=1,nxi
          do j=1,nxj
              x(i,j,ind(i,j)) = x(i,j,ind(i,j)) + 1
          end do
      end do

      RETURN
      END
      
      SUBROUTINE qextract(x,n,q,out,bin,nxi,nxj,nxk,nq)
cf2py intent(hide) nxi,nxj,nxk,nq
cf2py intent(out) out
cf2py threadsafe
      INTEGER x(nxi,nxj,nxk), nxi, nxj, i, j, k, l
      INTEGER nxk, nq, n 
      DOUBLE PRECISION q(nq), bin(nxk), out(nxi,nxj,nq)
      DOUBLE PRECISION cusum, next

      do i=1,nxi
          do j=1,nxj
              cusum = 0.0D0
              do k=1,nq
                  next = q(1)*n
                  l = 0
                  do while (cumsum.LT.next)
                      l = l + 1
                      cumsum = cumsum + x(i,j,l)
                  end do
                  out(i,j,k) = bin(l)
              end do
          end do
      end do

      RETURN
      END