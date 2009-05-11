      SUBROUTINE multiinc(x,ind,nxi,nxk)
cf2py intent(hide) nxi,nxk
cf2py intent(inplace) x
cf2py threadsafe
      INTEGER x(nxi,nxk), ind(nxi), nxi
      INTEGER nxk, i, k
      
      do i=1,nxi
          k = min(ind(i)+1, nxk)
          x(i,k) = x(i,k) + 1
      end do

      RETURN
      END
      
      SUBROUTINE qextract(x,n,q,out,bin,nxi,nxk,nq)
cf2py intent(hide) nxi,nxk,nq
cf2py intent(out) out
cf2py threadsafe
      INTEGER x(nxi,nxk), nxi, i, k, l
      INTEGER nxk, nq, n 
      DOUBLE PRECISION q(nq), bin(nxk), out(nq, nxi)
      DOUBLE PRECISION cusum, next

      do i=1,nxi
          cusum = 0.0D0
          l = 0      
!           print *,i,nxi,cusum,l
!           print *,
          do k=1,nq
              out(k,i) = 0.0D0
              next = q(k)*n
              do while (cusum.LT.next)
!                   print *,l,k,cusum,next
                  l = l + 1
                  cusum = cusum + x(i,l)
              end do
!               print *,k,next,cusum,l,n
!               print *,
              out(k,i) = bin(l)
          end do
      end do

      RETURN
      END