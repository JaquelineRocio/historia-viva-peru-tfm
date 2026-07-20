import { ArrayMaxSize, ArrayMinSize, IsArray, IsBoolean, IsIn, IsInt, IsNotEmpty, IsOptional, IsString, IsUrl, IsUUID, Max, MaxLength, Min, ValidateNested } from 'class-validator';
import { Transform, Type } from 'class-transformer';

export class CreateProjectDto {
  @IsString() @IsNotEmpty() @MaxLength(200) name!: string;
  @IsOptional() @IsString() description?: string;
  @IsOptional() @IsInt() @Min(-5000) @Max(3000) periodStart?: number;
  @IsOptional() @IsInt() @Min(-5000) @Max(3000) periodEnd?: number;
}

export class CreateYoutubeResourceDto {
  @IsUrl({ require_tld: false }) url!: string;
  @IsString() @IsNotEmpty() @MaxLength(300) title!: string;
  @IsOptional() @IsString() @MaxLength(200) author?: string;
  @IsBoolean() rightsConfirmed!: boolean;
}

export class PdfMetadataDto {
  @IsString() @IsNotEmpty() @MaxLength(300) title!: string;
  @IsOptional() @IsString() @MaxLength(200) author?: string;
  @IsOptional() @IsString() @MaxLength(80) license?: string;
  @IsOptional() @IsUrl({ require_tld: false }) sourceUrl?: string;
  @Transform(({ value }) => value === true || value === 'true')
  @IsBoolean() rightsConfirmed!: boolean;
}

export class UpdateResourceMetadataDto {
  @IsOptional() @IsString() @IsNotEmpty() @MaxLength(300) title?: string;
  @IsOptional() @IsString() @MaxLength(200) author?: string;
  @IsOptional() @IsString() @MaxLength(80) license?: string;
  @IsOptional() @IsUrl({ require_tld: false }) sourceUrl?: string;
}

export class ReviewSegmentDto {
  @IsIn(['reviewed', 'ambiguous', 'excluded']) status!: 'reviewed' | 'ambiguous' | 'excluded';
  @IsOptional() @IsString() labelKey?: string;
}

export class BulkReviewSegmentsDto extends ReviewSegmentDto {
  @IsArray() @ArrayMinSize(1) @ArrayMaxSize(200) @IsUUID('4', { each: true })
  segmentIds!: string[];
}

export class SegmentsQueryDto {
  @IsOptional() @Transform(({ value }) => value === undefined ? 1 : Number(value)) @IsInt() @Min(1)
  page = 1;
  @IsOptional() @Transform(({ value }) => value === undefined ? 30 : Number(value)) @IsInt() @Min(1) @Max(100)
  limit = 30;
  @IsOptional() @IsIn(['pending', 'reviewed', 'ambiguous', 'excluded'])
  status?: 'pending' | 'reviewed' | 'ambiguous' | 'excluded';
  @IsOptional() @IsString() @MaxLength(60) label?: string;
  @IsOptional() @IsIn(['document', 'low_confidence']) sort?: 'document' | 'low_confidence';
  @IsOptional() @IsUUID() campaignId?: string;
}

export class EvidenceFeedbackDto {
  @IsIn(['useful', 'irrelevant', 'incorrect']) value!: 'useful' | 'irrelevant' | 'incorrect';
  @IsOptional() @IsString() @MaxLength(1000) note?: string;
}

export class CorpusResourceDto {
  @IsIn(['candidate', 'included', 'excluded'])
  status!: 'candidate' | 'included' | 'excluded';

  @IsOptional()
  @IsIn(['book', 'academic', 'documentary', 'lecture', 'archive', 'other'])
  sourceStyle?: string;

  @IsOptional()
  @IsString()
  notes?: string;
}

export class CreateCollectionDto {
  @IsString() @IsNotEmpty() @MaxLength(200) name!: string;
  @IsOptional() @IsString() description?: string;
}

export class AddCollectionItemDto {
  @IsUUID() segmentId!: string;
  @IsOptional() @IsString() @MaxLength(1000) note?: string;
}

export class PublicationDecisionDto {
  @IsIn(['approved', 'rejected']) status!: 'approved' | 'rejected';
  @IsOptional() @IsString() @MaxLength(1000) note?: string;
}

export class SearchFiltersDto {
  @IsOptional() @IsString() @MaxLength(200) person?: string;
  @IsOptional() @IsString() @MaxLength(200) place?: string;
  @IsOptional() @Transform(({ value }) => value === undefined || value === '' ? undefined : Number(value))
  @IsInt() @Min(1000) @Max(2100) yearStart?: number;
  @IsOptional() @Transform(({ value }) => value === undefined || value === '' ? undefined : Number(value))
  @IsInt() @Min(1000) @Max(2100) yearEnd?: number;
  @IsOptional() @IsString() @MaxLength(60) label?: string;
}

export class SearchQueryDto extends SearchFiltersDto {
  @IsString() @IsNotEmpty() @MaxLength(1000) q!: string;
}

export class AssistantQueryDto extends SearchFiltersDto {
  @IsString() @IsNotEmpty() @MaxLength(1000) query!: string;
}

export class ReviewedEntityDto {
  @IsIn(['person', 'place', 'organization', 'date', 'period', 'other'])
  type!: 'person' | 'place' | 'organization' | 'date' | 'period' | 'other';
  @IsString() @IsNotEmpty() @MaxLength(300) text!: string;
  @IsOptional() @IsInt() @Min(1000) @Max(2100) yearStart?: number;
  @IsOptional() @IsInt() @Min(1000) @Max(2100) yearEnd?: number;
}

export class ReplaceEntitiesDto {
  @IsArray() @ValidateNested({ each: true }) @Type(() => ReviewedEntityDto)
  entities!: ReviewedEntityDto[];
}
