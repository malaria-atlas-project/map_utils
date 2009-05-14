      SUBROUTINE multiinc(x,ind,nxi,nxk)
cf2py intent(hide) nxi,nxk
cf2py intent(inplace) x
cf2py threadsafe
      INTEGER x(nxi,nxk), ind(nxi), nxi
      INTEGER nxk, i, k
      
      do i=1,nxi
          k = max(1, min(ind(i)+1, nxk))
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
     

      SUBROUTINE iinvlogit(C,nx,cmin,cmax)

cf2py intent(inplace) C
cf2py integer intent(in), optional :: cmin = 0
cf2py integer intent(in), optional :: cmax = -1
cf2py intent(hide) nx,ny
cf2py threadsafe

      DOUBLE PRECISION C(nx)
      INTEGER nx, i, cmin, cmax

      EXTERNAL DSCAL

      if (cmax.EQ.-1) then
          cmax = nx
      end if


        do i=cmin+1,cmax
            C(i) = 1.0D0 / (1.0D0 + dexp(-C(i)))
        end do


      RETURN
      END   


      SUBROUTINE iaaxpy(a,x,y,n,cmin,cmax)

cf2py intent(inplace) y
cf2py intent(in) x,a
cf2py integer intent(in), optional :: cmin = 0
cf2py integer intent(in), optional :: cmax = -1
cf2py intent(hide) n
cf2py threadsafe

      DOUBLE PRECISION y(n)
      DOUBLE PRECISION x(n),a
      INTEGER n, cmin, cmax
      EXTERNAL DAXPY

      if (cmax.EQ.-1) then
          cmax = n
      end if


      CALL DAXPY(cmax-cmin,a,x(cmin+1),1,y(cmin+1),1)


      RETURN
      END


      SUBROUTINE iaadd(C,A,nx,ny,cmin,cmax)

cf2py intent(inplace) C
cf2py intent(in) A
cf2py integer intent(in), optional :: cmin = 0
cf2py integer intent(in), optional :: cmax = -1
cf2py intent(hide) nx,ny
cf2py threadsafe

      DOUBLE PRECISION C(nx,ny)
      DOUBLE PRECISION A
      INTEGER nx, ny, i, j, cmin, cmax

      EXTERNAL DSCAL

      if (cmax.EQ.-1) then
          cmax = ny
      end if


        do j=cmin+1,cmax
            do i=1,nx
                C(i,j) = C(i,j) + A(i,j)
            end do
 !          CALL DSCAL(nx,a,C(1,j),1)
        enddo



      RETURN
      END
      

      SUBROUTINE iasq(C,nx,ny,cmin,cmax)

cf2py intent(inplace) C
cf2py integer intent(in), optional :: cmin = 0
cf2py integer intent(in), optional :: cmax = -1
cf2py intent(hide) nx,ny
cf2py threadsafe

      DOUBLE PRECISION C(nx,ny), cn
      INTEGER nx, ny, i, j, cmin, cmax

      EXTERNAL DSCAL

      if (cmax.EQ.-1) then
          cmax = ny
      end if


        do j=cmin+1,cmax
            do i=1,nx
                cn = C(i,j)
                C(i,j) = cn * cn
            end do
 !          CALL DSCAL(nx,a,C(1,j),1)
        enddo


      RETURN
      END


      SUBROUTINE iamul(C,A,nx,ny,cmin,cmax)

cf2py intent(inplace) C
cf2py intent(in) A
cf2py integer intent(in), optional :: cmin = 0
cf2py integer intent(in), optional :: cmax = -1
cf2py intent(hide) nx,ny
cf2py threadsafe

      DOUBLE PRECISION C(nx,ny)
      DOUBLE PRECISION A(nx,ny)
      INTEGER nx, ny, i, j, cmin, cmax

      EXTERNAL DSCAL

      if (cmax.EQ.-1) then
          cmax = ny
      end if


        do j=cmin+1,cmax
            do i=1,nx
                C(i,j) = C(i,j) * A(i,j)
            end do
 !          CALL DSCAL(nx,a,C(1,j),1)
        enddo


      RETURN
      END
