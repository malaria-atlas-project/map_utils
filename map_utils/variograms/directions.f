! Author: Anand Patil
! September 18, 2007
! GPL 2.0
! WARNING: Segmentation faults under Fortran 77, but not Fortran 95.


      SUBROUTINE dvar(d,nd,x,nb,r,m,a,na,h,blf,bw,bl,c,N)
cf2py double precision intent(optional):: r=6378.1
cf2py double precision intent(optional):: m=-1.0
cf2py intent(out) blf, bw, bl, c, N
cf2py intent(hide) nd, na

! Input:
! d(nd,nd): response variable
! x(nd,2): locations in [long, lat] form, in radians
! nb: number of bins
! a(na): vector of central angles
! h: halfwidth angle
! 
! Optional input:
! r: radius of the 'earth'
! m: distance of maximum bin
! 
! Output:
! blf(nb): left edges of bins
! bw(nb): width of bins
! bl(nb): centers of bins
! c(na,nb): actual variogram
! N(na,nb): number of pairs in each bin


      DOUBLE PRECISION d(nd), x(nd,2), a(na), h, r, m
      DOUBLE PRECISION blf(nb), bw, bl(nb), c(na,nb)
      DOUBLE PRECISION aa(2), ab(2), angle
      INTEGER nd,nb,na,N(na,nb),i,j,k,b
      LOGICAL flag
      DOUBLE PRECISION dist(nd,nd)
      DOUBLE PRECISION PI, delta
      PARAMETER (PI=3.141592653589793238462643d0)
      
      EXTERNAL dmax 

        CALL dist_geographic(dist,x,x,nd,nd,TRUE)

        if (m.LE.0.0D0) then
            m=0.0D0
            do i=1,nd-1
                do j=i+1,nd
                    if (dist(i,j)*r.GT.m) then
                        m=dist(i,j)*r
                    end if
                end do
            end do
        end if

        bw = m / nb
        blf(1) = 0
        bl(1) = bw*0.5D0
        do i=2,nb
            blf(i) = blf(i-1) + bw
            bl(i) = bl(i-1) + bw
        enddo

        
        do i=1,na
            do j=1,nb
                N(i,j)=0
                c(i,j)=0.0D0
            end do
        end do
            
        do i=1,nd-1
            do j=i+1,nd
                
!               Find bin
                flag=.TRUE.
                if (dist(i,j).GT.0.0D0) then                    
                    do k=1,nb
                        if (FLAG) then
                            if ((dist(i,j)*r.LE.blf(k)+bw)) then
                                flag=.FALSE.
                                b=k
                            end if
                        end if
                    end do
                end if
                if (.not.flag) then

!                   Find angle
                    do k=1,2
                        aa(k) = x(i,k)
                        ab(k) = x(j,k)
                    end do
                   CALL angle_geographic(aa,ab,dist(i,j),angle)
!                   angle = ang(i,j)
                
!                   Add pair to appropriate bin.
                    do k=1,na
                        delta = dmod(dabs(angle-a(k)),pi)
                        if ((delta.LT.h).OR.((pi-delta).LT.h)) then
                            N(k,b)=N(k,b)+1
                            c(k,b)=c(k,b)*(N(k,b))/(N(k,b)+1)
                            c(k,b)=c(k,b)+(d(i)-d(j))**2/(N(k,b)+1)
                        end if
                    end do
                end if
            end do
        end do
        
!         Add self-pairs (zero distances)
!         Or maybe not... geoR doesn't do this, and it kind of doesn't make sense to do it.
!         do k=1,na
!             c(k,1)=c(k,1)*N(k,1)/(N(k,1)+nd*0.5D0)
!         end do
      
      RETURN
      END

      SUBROUTINE dist_geographic(D,x,y,nx,ny,symm)
! First coordinate is longitude, second is latitude.
! Assumes r=1.

cf2py intent(out) D
cf2py logical intent(optional) :: symm = 0
cf2py intent(hide) nx
cf2py intent(hide) ny

      DOUBLE PRECISION D(nx,ny), x(nx,2), y(ny,2)
      integer nx,ny,i,j,j_lo
      LOGICAL symm
      DOUBLE PRECISION t1, t2, t3, t4, t5, t6
      DOUBLE PRECISION dl, phi1, phi2
      DOUBLE PRECISION sphi1, sphi2, cphi1, cphi2, sdl, cdl
      
      do i=1,nx
        phi1 = x(i,2)
        
        sphi1 = dsin(phi1)
        cphi1 = dcos(phi1)
        
        if(symm) then
            D(i,i)=0.0D0            
            j_lo = i+1
        else 
            j_lo = 1
        endif
        do j=j_lo,ny
            phi2 = y(j,2)

            sphi2 = dsin(phi2)
            cphi2 = dcos(phi2)

            dl = x(i,1) - y(j,1)

            sdl = dsin(dl)
            cdl = dcos(dl)

            t1 = (cphi2 * sdl) ** 2

            t2 = cphi1*sphi2
            t3 = sphi1*cphi2*cdl
            t4 = (t2-t3)**2

            t5 = sphi1*sphi2
            t6 = cphi1*cphi2*cdl

            D(i,j) = DATAN2(dsqrt(t1+t4),(t5+t6))                      
            if(symm) then                  
                D(j,i) = D(i,j)
            end if
        enddo          
      enddo
      RETURN
      END      
      
      SUBROUTINE angle_geographic(A,B,D,angle)

! Finds angle of inclination of vector pointing from A to B on sphere
! First coordinate is longitude, second is latitude.
! Assumes r=1.

cf2py intent(out) angle

      DOUBLE PRECISION A(2), B(2), al, bl, sterm, cterm
      DOUBLE PRECISION D, angle
          
      if (D.EQ.0.0D0) then
          angle=-999999D0
          RETURN
      end if
      
      al = B(2)-A(2)
      bl = B(1)-A(1)

!       Optimization opportunity: sin(D) and cos(D) were already found in
!       dist_geographic. If you combine the angle- and dist-finders, you could
!       take advantage of this. Also, note bl here = dl in dist finder, so you
!       can save those trig operations too.
      sterm = dsin(al)/dsin(D)
      if (bl.EQ.0.0D0) then
          cterm = 0.0D0
      else
          cterm = (dcos(al)-dcos(bl)*dcos(D))/dsin(bl)/dsin(D)
      end if
      
      angle = datan2(sterm, cterm)
      
      RETURN
      END

      SUBROUTINE aniso_geo_rad(D,x,y,nx,ny,inc,ecc,symm)
! First coordinate is longitude, second is latitude.
! Assumes r=1.

cf2py intent(out) D
cf2py logical intent(optional) :: symm = 0
cf2py intent(hide) nx
cf2py intent(hide) ny

      DOUBLE PRECISION D(nx,ny), x(nx,2), y(ny,2)
      integer nx,ny,i,j,j_lo
      LOGICAL symm
      DOUBLE PRECISION t1, t2, t3, t4, t5, t6
      DOUBLE PRECISION dl, phi1, phi2, theta, inc, ecc, dtheta
      DOUBLE PRECISION sphi1, sphi2, cphi1, cphi2, sdl, cdl
      
      do i=1,nx
        phi1 = x(i,2)
        
        sphi1 = dsin(phi1)
        cphi1 = dcos(phi1)
        
        if(symm) then
            D(i,i)=0.0D0            
            j_lo = i+1
        else 
            j_lo = 1
        endif
        do j=j_lo,ny
            phi2 = y(j,2)

            sphi2 = dsin(phi2)
            cphi2 = dcos(phi2)

            dl = x(i,1) - y(j,1)

            sdl = dsin(dl)
            cdl = dcos(dl)

            t1 = (cphi2 * sdl) ** 2

            t2 = cphi1*sphi2
            t3 = sphi1*cphi2*cdl
            t4 = (t2-t3)**2

            t5 = sphi1*sphi2
            t6 = cphi1*cphi2*cdl

            D(i,j) = DATAN2(dsqrt(t1+t4),(t5+t6))
            
            CALL angle_geographic(x(i,1), y(j,1), D(i,j), theta)
            dtheta = theta-ecc
            D(i,j) = D(i,j) / dsqrt(1.0D0 - ecc**2 * dcos(dtheta)**2)
                                  
            if(symm) then                  
                D(j,i) = D(i,j)
            end if
        enddo          
      enddo
      RETURN
      END