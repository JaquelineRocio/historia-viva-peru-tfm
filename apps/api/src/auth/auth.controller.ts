import { Body, Controller, Get, HttpCode, Post, Req, UseGuards } from '@nestjs/common';
import type { Request } from 'express';
import { ApiBearerAuth, ApiOperation, ApiTags } from '@nestjs/swagger';
import { AuthService } from './auth.service';
import { LoginDto } from './dto/login.dto';
import { JwtAuthGuard } from './jwt-auth.guard';
import { CurrentUser } from './current-user.decorator';
import { AuthUser } from './jwt.strategy';
import { LoginThrottleService } from './login-throttle.service';

@ApiTags('auth')
@Controller('auth')
export class AuthController {
  constructor(
    private readonly authService: AuthService,
    private readonly throttle: LoginThrottleService,
  ) {}

  @Post('login')
  @HttpCode(200)
  @ApiOperation({ summary: 'Login usuario/contraseña → JWT' })
  async login(@Body() dto: LoginDto, @Req() request: Request) {
    const key = `${request.ip || 'unknown'}:${dto.username.trim().toLowerCase()}`;
    this.throttle.assertAllowed(key);
    try {
      const result = await this.authService.login(dto);
      this.throttle.clear(key);
      return result;
    } catch (error) {
      this.throttle.registerFailure(key);
      throw error;
    }
  }

  @Get('me')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Usuario autenticado actual' })
  me(@CurrentUser() user: AuthUser) {
    return user;
  }
}
