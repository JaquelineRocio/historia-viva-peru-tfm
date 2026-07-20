import { ApiProperty } from '@nestjs/swagger';
import { IsNotEmpty, IsString, MaxLength, MinLength } from 'class-validator';

export class LoginDto {
  @ApiProperty({ example: 'docente' })
  @IsString()
  @IsNotEmpty()
  @MaxLength(80)
  username!: string;

  @ApiProperty({ example: 'tfm2026' })
  @IsString()
  @IsNotEmpty()
  @MinLength(4)
  @MaxLength(200)
  password!: string;
}
